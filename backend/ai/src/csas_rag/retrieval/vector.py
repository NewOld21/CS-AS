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
        where = None
        if concept_ids:
            # Chroma stores the reviewed array as canonical JSON because metadata values are scalar.
            where = {"concept_ids": json.dumps(sorted(concept_ids), separators=(",", ":"))}
        return self.store.query(vector, limit, where)
