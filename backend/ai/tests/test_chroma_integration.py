import os
import sys
import unittest
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from csas_rag.indexing.pipeline import build_index
from csas_rag.providers.chroma import ChromaVectorStore
from csas_rag.providers.embeddings import DeterministicTestEmbedding
from csas_rag.retrieval.vector import VectorRetriever


def document():
    return {"source_id": "fixture", "document_id": "doc:process", "revision": "r1",
            "title": "Process and thread",
            "content": "# Process and thread\n\nA process owns memory. A thread shares process memory.\n",
            "source_url": "https://example.test/process", "locator": "process.md",
            "category": "operating-system", "concept_ids": ["concept:process"], "language": "en"}


@unittest.skipUnless(os.environ.get("CSAS_CHROMA_INTEGRATION") == "1", "requires live ChromaDB")
class ChromaIntegrationTests(unittest.TestCase):
    def test_upsert_is_idempotent_and_query_returns_metadata(self):
        version = "integration-" + uuid.uuid4().hex
        store = ChromaVectorStore(version)
        try:
            embedding = DeterministicTestEmbedding(32)
            manifest = build_index([document()], store, embedding, version, "fixture")
            build_index([document()], store, embedding, version, "fixture")
            result = VectorRetriever(store, embedding, manifest).search("process thread memory")
            self.assertEqual(store.collection.count(), manifest["chunk_count"])
            self.assertEqual(result[0]["metadata"]["document_id"], "doc:process")
        finally:
            store.delete_index()


if __name__ == "__main__":
    unittest.main()
