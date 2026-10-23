"""Vector retrieval using the exact embedding configuration of an index."""
import json
import math
import hashlib
from collections import OrderedDict
from threading import Lock
from .planning import validate_filters


class VectorRetriever:
    def __init__(self, store, embedding, index_manifest: dict):
        if embedding.model != index_manifest["model"] or embedding.dimensions != index_manifest["dimensions"]:
            raise ValueError("Query embedding does not match the index")
        self.store = store
        self.embedding = embedding
        self.manifest = index_manifest
        self._vectors = OrderedDict()
        self._lock = Lock()

    def search(self, question: str, limit: int = 5, concept_ids: list[str] | None = None,
               filters: dict | None = None, search_type: str = "similarity") -> list[dict]:
        question = question.strip()
        if not question or len(question) > 2000 or not 1 <= limit <= 20:
            raise ValueError("Invalid retrieval request")
        key = hashlib.sha256(question.encode("utf-8")).hexdigest()
        with self._lock:
            if key in self._vectors:
                self._vectors.move_to_end(key)
                vector = self._vectors[key]
            else:
                vector = self.embedding.embed([question])[0]
                self._vectors[key] = vector
                if len(self._vectors) > 128:
                    self._vectors.popitem(last=False)
        filters = validate_filters(filters or {})
        if search_type not in ("similarity", "mmr"):
            raise ValueError("Invalid search type")
        where = None if not filters else ({k: v for k, v in filters.items()} if len(filters) == 1
                   else {"$and": [{k: v} for k, v in filters.items()]})
        if not concept_ids and not filters and search_type == "similarity":
            return self.store.query(vector, limit)
        # Chroma metadata is scalar, so reviewed concept arrays are stored as JSON. Fetch a
        # bounded semantic candidate set, rank membership matches first, then fill from the
        # global results. This implements concept-first retrieval without turning an absent or
        # partial mapping into an empty answer.
        count = min(20, max(limit * 4, limit)) if concept_ids or search_type == "mmr" else limit
        candidates = (self.store.query(vector, count, where=where) if where
                      else self.store.query(vector, count))
        # Recheck SDK/store results; no model can claim a filter was applied.
        candidates = [r for r in candidates if all(r.get("metadata", {}).get(k) == v for k, v in filters.items())]
        requested = set(concept_ids or [])

        def concepts(row: dict) -> set[str]:
            value = row.get("metadata", {}).get("concept_ids", [])
            if isinstance(value, str):
                try:
                    value = json.loads(value)
                except json.JSONDecodeError:
                    value = []
            return set(value) if isinstance(value, list) else set()

        matched = [row for row in candidates if requested & concepts(row)]
        fallback = [row for row in candidates if not requested & concepts(row)]
        ranked = matched + fallback
        if search_type == "mmr":
            vectors = self.store.get_embeddings([r["chunk_id"] for r in ranked])
            selected = []
            def cosine(a, b):
                denominator = math.sqrt(sum(x*x for x in a) * sum(x*x for x in b))
                return sum(x*y for x, y in zip(a, b)) / denominator if denominator else 0.0
            while ranked and len(selected) < limit:
                def score(row):
                    current = vectors[row["chunk_id"]]
                    redundancy = max((cosine(current, vectors[r["chunk_id"]]) for r in selected), default=0)
                    return 0.5 * cosine(vector, current) - 0.5 * redundancy
                best = max(ranked, key=score)
                selected.append(best)
                ranked.remove(best)
            return selected
        return ranked[:limit]
