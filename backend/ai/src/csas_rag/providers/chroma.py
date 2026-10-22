"""ChromaDB adapter; SDK imports stay outside domain code."""
import json
import os
import tempfile


class ChromaVectorStore:
    def __init__(self, index_version: str, host=None, port=None):
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory(prefix="csas-chroma-import-") as directory:
            try:
                os.chdir(directory)
                import chromadb
            finally:
                os.chdir(original_cwd)

        client = chromadb.HttpClient(
            host=host or os.environ.get("CHROMA_HOST", "localhost"),
            port=int(port or os.environ.get("CHROMA_PORT", "8000")),
            settings=chromadb.Settings(_env_file=None),
        )
        name = "csas-" + index_version.replace("_", "-")
        self.client = client
        self.name = name
        try:
            self.collection = client.get_or_create_collection(
                name, embedding_function=None, configuration={"hnsw": {"space": "cosine"}}
            )
        except TypeError:  # Compatibility with the pinned client API.
            self.collection = client.get_or_create_collection(
                name, embedding_function=None, metadata={"hnsw:space": "cosine"}
            )

    @staticmethod
    def metadata(chunk: dict, index_version: str) -> dict:
        return {
            "source_id": chunk["source_id"],
            "document_id": chunk["document_id"],
            "revision": chunk["revision"],
            "chunk_id": chunk["chunk_id"],
            "title": chunk["title"],
            "url": chunk["source_url"],
            "locator": chunk["locator"],
            "category": chunk.get("category") or "",
            "language": chunk["language"],
            "concept_ids": json.dumps(sorted(chunk.get("concept_ids", [])), separators=(",", ":")),
            "chunk_index": chunk["chunk_index"],
            "chunk_config_version": chunk["chunk_config_version"],
            "index_version": index_version,
        }

    def replace_document(self, chunks: list[dict], embeddings: list[list[float]], index_version: str) -> None:
        document_id = chunks[0]["document_id"]
        saved = self.collection.get(where={"document_id": document_id})
        current_ids = {chunk["chunk_id"] for chunk in chunks}
        stale = [identifier for identifier in saved["ids"] if identifier not in current_ids]
        if stale:
            self.collection.delete(ids=stale)
        self.collection.upsert(
            ids=[chunk["chunk_id"] for chunk in chunks],
            embeddings=embeddings,
            documents=[chunk["content"] for chunk in chunks],
            metadatas=[self.metadata(chunk, index_version) for chunk in chunks],
        )

    def query(self, embedding: list[float], limit: int, where: dict | None = None) -> list[dict]:
        result = self.collection.query(
            query_embeddings=[embedding], n_results=limit, where=where, include=["documents", "metadatas", "distances"]
        )
        rows = []
        for identifier, document, metadata, distance in zip(
            result["ids"][0], result["documents"][0], result["metadatas"][0], result["distances"][0]
        ):
            rows.append({"chunk_id": identifier, "content": document, "metadata": metadata,
                         "distance": float(distance), "score": max(-1.0, min(1.0, 1.0 - float(distance)))})
        return rows

    def delete_index(self) -> None:
        self.client.delete_collection(self.name)
