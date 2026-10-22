import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from csas_rag.indexing.pipeline import ChunkConfig, activate_manifest, build_index, chunk_document, write_manifest
from csas_rag.providers.embeddings import DeterministicTestEmbedding
from csas_rag.retrieval.vector import VectorRetriever


class MemoryStore:
    def __init__(self):
        self.rows = {}

    def replace_document(self, chunks, embeddings, index_version):
        document_id = chunks[0]["document_id"]
        self.rows = {key: value for key, value in self.rows.items() if value[0]["document_id"] != document_id}
        self.rows.update({chunk["chunk_id"]: (chunk, embedding) for chunk, embedding in zip(chunks, embeddings)})

    def query(self, vector, limit, where=None):
        rows = []
        for chunk, embedding in self.rows.values():
            if where and json.dumps(sorted(chunk["concept_ids"]), separators=(",", ":")) != where["concept_ids"]:
                continue
            score = sum(a * b for a, b in zip(vector, embedding))
            rows.append({"chunk_id": chunk["chunk_id"], "content": chunk["content"],
                         "metadata": chunk, "distance": 1 - score, "score": score})
        return sorted(rows, key=lambda row: row["score"], reverse=True)[:limit]


def document(content="# Process and thread\n\nA process owns memory. A thread shares process memory.\n"):
    return {"source_id": "fixture", "document_id": "doc:process", "revision": "r1",
            "title": "Process and thread", "content": content, "source_url": "https://example.test/process",
            "locator": "process.md", "category": "operating-system", "concept_ids": ["concept:process"],
            "language": "en"}


class IndexingTests(unittest.TestCase):
    def test_chunk_ids_are_stable_and_change_with_revision_or_config(self):
        first = chunk_document(document("# A\n\n" + "context sentence. " * 100), ChunkConfig(max_chars=300, overlap_chars=40))
        again = chunk_document(document("# A\n\n" + "context sentence. " * 100), ChunkConfig(max_chars=300, overlap_chars=40))
        changed = chunk_document({**document("# A\n\n" + "context sentence. " * 100), "revision": "r2"},
                                 ChunkConfig(max_chars=300, overlap_chars=40))
        self.assertEqual([x["chunk_id"] for x in first], [x["chunk_id"] for x in again])
        self.assertNotEqual(first[0]["chunk_id"], changed[0]["chunk_id"])
        self.assertTrue(all(len(x["content"]) <= 480 for x in first))

    def test_index_is_idempotent_and_replaces_changed_document_chunks(self):
        store = MemoryStore()
        embedding = DeterministicTestEmbedding(32)
        one = build_index([document()], store, embedding, "cs-test-v1", "corpus-1")
        two = build_index([document()], store, embedding, "cs-test-v1", "corpus-1")
        self.assertEqual((one["chunk_count"], len(store.rows)), (two["chunk_count"], len(store.rows)))
        changed = {**document("# Changed\n\nNew revision about locks."), "revision": "r2"}
        build_index([changed], store, embedding, "cs-test-v1", "corpus-2")
        self.assertTrue(all(row[0]["revision"] == "r2" for row in store.rows.values()))

    def test_search_preserves_citation_metadata_and_checks_model(self):
        store = MemoryStore()
        embedding = DeterministicTestEmbedding(32)
        manifest = build_index([document()], store, embedding, "cs-test-v1", "corpus-1")
        result = VectorRetriever(store, embedding, manifest).search("thread process memory", concept_ids=["concept:process"])
        self.assertEqual(result[0]["metadata"]["source_url"], "https://example.test/process")
        with self.assertRaises(ValueError):
            VectorRetriever(store, DeterministicTestEmbedding(16), manifest)

    def test_manifest_starts_building_and_is_written_atomically(self):
        store = MemoryStore()
        manifest = build_index([document()], store, DeterministicTestEmbedding(8), "cs-test-v1", "digest")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "index.json"
            write_manifest(path, manifest)
            self.assertEqual(json.loads(path.read_text())["status"], "BUILDING")

    def test_activation_requires_a_passed_retrieval_evaluation(self):
        manifest = build_index([document()], MemoryStore(), DeterministicTestEmbedding(8), "cs-test-v1", "digest")
        with self.assertRaises(ValueError):
            activate_manifest(manifest, {"passed": False, "query_count": 5})
        active = activate_manifest(manifest, {"passed": True, "query_count": 5, "top5_hit_rate": 1.0})
        self.assertEqual(active["status"], "ACTIVE")


if __name__ == "__main__":
    unittest.main()
