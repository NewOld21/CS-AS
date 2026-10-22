import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from csas_rag.indexing.pipeline import (ChunkConfig, activate_manifest, build_index, chunk_document,
                                        incremental_index, write_manifest)
from csas_rag.providers.embeddings import DeterministicTestEmbedding
from csas_rag.retrieval.vector import VectorRetriever


class MemoryStore:
    def __init__(self):
        self.rows = {}
        self.replace_calls = 0
        self.remove_calls = 0
        self.fail_replace = False
        self.fail_remove = False

    def replace_document(self, chunks, embeddings, index_version):
        self.replace_calls += 1
        if self.fail_replace:
            raise RuntimeError("store unavailable")
        document_id = chunks[0]["document_id"]
        self.rows = {key: value for key, value in self.rows.items() if value[0]["document_id"] != document_id}
        self.rows.update({chunk["chunk_id"]: (chunk, embedding) for chunk, embedding in zip(chunks, embeddings)})

    def document_chunk_ids(self, document_id):
        return [key for key, value in self.rows.items() if value[0]["document_id"] == document_id]

    def get_embeddings(self, chunk_ids):
        return {key: self.rows[key][1] for key in chunk_ids if key in self.rows}

    def remove_document(self, document_id):
        self.remove_calls += 1
        if self.fail_remove:
            raise RuntimeError("delete unavailable")
        self.rows = {key: value for key, value in self.rows.items()
                     if value[0]["document_id"] != document_id}

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


class CountingEmbedding(DeterministicTestEmbedding):
    def __init__(self, dimensions=32, model="counting-test-v1"):
        super().__init__(dimensions)
        self.model = model
        self.calls = 0
        self.inputs = 0
        self.fail = False

    def embed(self, texts):
        self.calls += 1
        self.inputs += len(texts)
        if self.fail:
            raise RuntimeError("embedding unavailable")
        return super().embed(texts)


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

    def test_concept_search_prioritizes_matches_and_falls_back_to_global_rows(self):
        store = MemoryStore()
        embedding = DeterministicTestEmbedding(32)
        mapped = document("# Thread\n\nThread memory and scheduling.")
        unrelated = {**document("# Other\n\nThread memory overview."),
                     "document_id": "doc:other", "concept_ids": [], "locator": "other.md"}
        manifest = build_index([unrelated, mapped], store, embedding, "cs-test-v1", "corpus-1")
        retriever = VectorRetriever(store, embedding, manifest)
        matched = retriever.search("thread memory", limit=2, concept_ids=["concept:process"])
        self.assertEqual(matched[0]["metadata"]["document_id"], "doc:process")
        fallback = retriever.search("thread memory", limit=2, concept_ids=["concept:not-mapped"])
        self.assertEqual(len(fallback), 2)

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

    def test_incremental_first_run_and_identical_rerun_skip_embedding_and_upsert(self):
        store = MemoryStore()
        embedding = CountingEmbedding()
        manifest, first = incremental_index([document()], store, embedding, "cs-test-v1", "one")
        self.assertEqual((first["new"], first["embedded_documents"]), (1, 1))
        first_inputs, first_writes = embedding.inputs, store.replace_calls
        manifest, second = incremental_index([document()], store, embedding, "cs-test-v1", "one", manifest)
        self.assertEqual((second["unchanged"], second["skipped_documents"]), (1, 1))
        self.assertEqual((embedding.inputs, store.replace_calls), (first_inputs, first_writes))
        self.assertEqual(manifest["schema_version"], 2)
        self.assertEqual(manifest["documents"][0]["content_hash"],
                         __import__("hashlib").sha256(document()["content"].encode()).hexdigest())

    def test_incremental_add_modify_reuses_equal_chunks_and_deletes_only_complete_source(self):
        store = MemoryStore()
        embedding = CountingEmbedding()
        config = ChunkConfig(max_chars=300, overlap_chars=0, min_chars=20, version="test-chunks-v1")
        original = document("# Stable\n\n" + "same sentence. " * 12
                            + "\n# Changed\n\n" + "old detail. " * 12)
        second = {**document("# Added\n\nnew document body"), "document_id": "doc:added",
                  "locator": "added.md"}
        manifest, _ = incremental_index([original], store, embedding, "cs-test-v1", "one", config=config)
        previous_inputs = embedding.inputs
        modified = {**original, "revision": "r2",
                    "content": "# Stable\n\n" + "same sentence. " * 12
                               + "\n# Changed\n\n" + "new detail. " * 12}
        manifest, changed = incremental_index([modified, second], store, embedding, "cs-test-v1", "two",
                                              manifest, config=config)
        self.assertEqual((changed["new"], changed["modified"]), (1, 1))
        self.assertGreaterEqual(changed["reused_chunks"], 1)
        self.assertLess(embedding.inputs - previous_inputs,
                        len(chunk_document(modified, config)) + len(chunk_document(second, config)))
        manifest, partial = incremental_index([modified], store, embedding, "cs-test-v1", "three",
                                              manifest, config=config)
        self.assertEqual((partial["deleted"], store.remove_calls), (0, 0))
        manifest, complete = incremental_index([modified], store, embedding, "cs-test-v1", "three",
                                               manifest, config=config,
                                               complete_source_ids={"fixture"})
        self.assertEqual((complete["deleted"], complete["removed_documents"]), (1, 1))
        self.assertFalse(store.document_chunk_ids("doc:added"))

    def test_incremental_setting_change_reembeds_and_dry_run_only_previews(self):
        store = MemoryStore()
        first_embedding = CountingEmbedding(model="model-a")
        manifest, _ = incremental_index([document()], store, first_embedding, "cs-test-v1", "one")
        changed_embedding = CountingEmbedding(model="model-b")
        preview_manifest, preview = incremental_index(
            [document()], store, changed_embedding, "cs-test-v1", "one", manifest, dry_run=True)
        self.assertIs(preview_manifest, manifest)
        self.assertEqual((preview["modified"], changed_embedding.inputs), (1, 0))
        manifest, changed = incremental_index(
            [document()], store, changed_embedding, "cs-test-v1", "one", manifest)
        self.assertEqual((changed["modified"], changed_embedding.inputs), (1, 1))

    def test_incremental_failures_keep_old_chunks_and_retry_idempotently(self):
        store = MemoryStore()
        embedding = CountingEmbedding()
        manifest, _ = incremental_index([document()], store, embedding, "cs-test-v1", "one")
        old_ids = set(store.rows)
        changed = {**document("# Changed\n\nA new body about mutexes."), "revision": "r2"}
        embedding.fail = True
        failed_manifest, failed = incremental_index(
            [changed], store, embedding, "cs-test-v1", "two", manifest)
        self.assertEqual((failed["failed_documents"], set(store.rows)), (1, old_ids))
        self.assertEqual(failed_manifest["documents"][0]["indexing_status"], "failed")
        embedding.fail = False
        recovered, retried = incremental_index(
            [changed], store, embedding, "cs-test-v1", "two", failed_manifest)
        self.assertEqual((retried["modified"], retried["failed_documents"]), (1, 0))
        self.assertEqual(recovered["documents"][0]["indexing_status"], "indexed")
        self.assertTrue(all(value[0]["revision"] == "r2" for value in store.rows.values()))

    def test_incremental_store_and_delete_failure_remain_retryable(self):
        store = MemoryStore()
        embedding = CountingEmbedding()
        manifest, _ = incremental_index([document()], store, embedding, "cs-test-v1", "one")
        old_ids = set(store.rows)
        changed = {**document("# Changed\n\nstore failure body"), "revision": "r2"}
        store.fail_replace = True
        failed_manifest, failed = incremental_index(
            [changed], store, embedding, "cs-test-v1", "two", manifest)
        self.assertEqual((failed["failed_documents"], set(store.rows)), (1, old_ids))
        store.fail_replace = False
        manifest, _ = incremental_index([changed], store, embedding, "cs-test-v1", "two", failed_manifest)
        store.fail_remove = True
        failed_delete_manifest, failed_delete = incremental_index(
            [], store, embedding, "cs-test-v1", "empty", manifest,
            complete_source_ids={"fixture"})
        self.assertEqual(failed_delete["failed_documents"], 1)
        self.assertEqual(failed_delete_manifest["documents"][0]["indexing_status"], "delete_failed")
        store.fail_remove = False
        recovered, retry = incremental_index(
            [], store, embedding, "cs-test-v1", "empty", failed_delete_manifest,
            complete_source_ids={"fixture"})
        self.assertEqual((retry["removed_documents"], recovered["document_count"]), (1, 0))


if __name__ == "__main__":
    unittest.main()
