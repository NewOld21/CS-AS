import json
import sys
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "backend/ai/src"))

from csas_rag.evaluation.retrieval import evaluate_retrieval, load_dataset, validate_dataset


class FakeRetriever:
    def __init__(self, rows_by_question):
        self.rows_by_question = rows_by_question

    def search(self, question, limit=5):
        return self.rows_by_question.get(question, [])[:limit]


def result(document_id, chunk_id, score=0.8):
    return {"chunk_id": chunk_id, "score": score, "distance": 1 - score,
            "metadata": {"document_id": document_id, "title": document_id,
                         "url": "https://example.org/" + document_id}}


def question(identifier, text, document_id="doc:one", chunks=None, evaluable=True):
    row = {"id": identifier, "category": "network", "question": text,
           "evaluable": evaluable,
           "relevant_documents": [{"document_id": document_id,
                                    "source_url": "https://example.org/source"}],
           "relevant_chunk_ids": chunks or []}
    if not evaluable:
        row["insufficient_reason"] = "not present in the approved corpus"
    return row


class RetrievalEvaluationTest(unittest.TestCase):
    def test_document_metrics_and_duplicate_chunks(self):
        dataset = {"version": "test-v1", "questions": [
            question("q1", "first"), question("q2", "second", "doc:two")
        ]}
        retriever = FakeRetriever({
            "first": [result("doc:one", "chunk:1"), result("doc:one", "chunk:2")],
            "second": [result("doc:other", "chunk:3"), result("doc:two", "chunk:4")],
        })
        report = evaluate_retrieval(dataset, retriever, {"index_version": "v1"})
        self.assertEqual(0.5, report["document_metrics"]["hit_rate@1"])
        self.assertEqual(1.0, report["document_metrics"]["hit_rate@3"])
        self.assertEqual(0.75, report["document_metrics"]["mrr"])
        self.assertEqual(["doc:one", "doc:one"], report["results"][0]["retrieved_document_ids"])
        self.assertEqual("not_evaluated", report["chunk_metrics"]["status"])

    def test_chunk_metrics_are_reported_separately(self):
        dataset = {"version": "test-v1", "questions": [question("q1", "first", chunks=["chunk:2"])]}
        report = evaluate_retrieval(dataset, FakeRetriever({"first": [
            result("doc:one", "chunk:1"), result("doc:one", "chunk:2")
        ]}), {"index_version": "v1"})
        self.assertEqual(0.0, report["chunk_metrics"]["hit_rate@1"])
        self.assertEqual(1.0, report["chunk_metrics"]["hit_rate@3"])
        self.assertEqual(0.5, report["chunk_metrics"]["mrr"])

    def test_insufficient_question_is_not_counted_as_retrieval_failure(self):
        dataset = {"version": "test-v1", "questions": [question("q1", "missing", evaluable=False)]}
        report = evaluate_retrieval(dataset, FakeRetriever({}), {"index_version": "v1"})
        self.assertEqual(0, report["evaluated_question_count"])
        self.assertEqual(1, report["insufficient_evidence_count"])
        self.assertEqual("insufficient_evidence", report["results"][0]["status"])

    def test_dataset_validation_rejects_placeholder_labels(self):
        bad = {"version": "test-v1", "questions": [question("q1", "bad", "fake-id")]}
        with self.assertRaises(ValueError):
            validate_dataset(bad)

    def test_committed_dataset_has_twenty_balanced_real_questions(self):
        dataset = load_dataset(ROOT / "harness/evals/retrieval-v1.json")
        self.assertEqual(20, len(dataset["questions"]))
        self.assertEqual({category: 4 for category in (
            "operating-system", "network", "database", "data-structure-algorithm",
            "software-distributed-systems")}, Counter(row["category"] for row in dataset["questions"]))
        corpus_path = ROOT / "data/processed/ingestion-live-v3/normalized.jsonl"
        if corpus_path.exists():
            corpus = [json.loads(line) for line in corpus_path.read_text(encoding="utf-8").splitlines()]
            actual = {(row["document_id"], row["source_url"]) for row in corpus}
            labels = {(document["document_id"], document["source_url"])
                      for row in dataset["questions"] for document in row["relevant_documents"]}
            self.assertTrue(labels <= actual)


if __name__ == "__main__":
    unittest.main()
