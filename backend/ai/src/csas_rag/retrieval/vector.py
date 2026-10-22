"""Vector retrieval using the exact embedding configuration of an index."""
import json


class VectorRetriever:
    def __init__(self, store, embedding, index_manifest: dict):
        if embedding.model != index_manifest["model"] or embedding.dimensions != index_manifest["dimensions"]:
            raise ValueError("Query embedding does not match the index")
        self.store = store
        self.embedding = embedding
        self.manifest = index_manifest

    def search(self, question: str, limit: int = 5, concept_ids: list[str] | None = None) -> list[dict]:
        question = question.strip()
        if not question or len(question) > 2000 or not 1 <= limit <= 20:
            raise ValueError("Invalid retrieval request")
        vector = self.embedding.embed([question])[0]
        if not concept_ids:
            return self.store.query(vector, limit)
        # Chroma metadata is scalar, so reviewed concept arrays are stored as JSON. Fetch a
        # bounded semantic candidate set, rank membership matches first, then fill from the
        # global results. This implements concept-first retrieval without turning an absent or
        # partial mapping into an empty answer.
        candidates = self.store.query(vector, min(20, max(limit * 4, limit)))
        requested = set(concept_ids)

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
        return (matched + fallback)[:limit]
