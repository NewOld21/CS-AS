import json
import sys
import threading
import unittest
from datetime import datetime, timedelta, timezone
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from csas_rag.api.server import handler
from csas_rag.generation.answering import AnswerService, GenerationError, SYSTEM_RULES


ROW = {"chunk_id": "chunk:one", "content": "A database index speeds reads but adds write maintenance cost.",
       "score": 0.9, "metadata": {"source_id": "fixture", "document_id": "doc:index", "revision": "r1",
       "title": "Database index", "url": "https://example.test/index", "locator": "index.md"}}


class Retriever:
    def __init__(self, rows=None):
        self.rows = [ROW] if rows is None else rows
        self.last_question = None

    def search(self, question, limit, concepts):
        self.last_question = question
        return self.rows


class Generator:
    model = "mock-answer-v1"

    def __init__(self, result=None, error=None):
        self.result = result or {"status": "answered", "answer": "인덱스는 읽기를 빠르게 하지만 쓰기 비용을 늘립니다.",
                                 "cited_chunk_ids": ["chunk:one"]}
        self.error = error
        self.system = None
        self.prompt = None

    def generate(self, system, prompt):
        self.system, self.prompt = system, prompt
        if self.error:
            raise self.error
        return self.result


def answer_request():
    return {"request_id": "req-1", "deadline_at": (datetime.now(timezone.utc) + timedelta(minutes=1)).isoformat(),
            "index_version": "cs-test-v1", "question": "인덱스는 왜 사용해?", "history": [],
            "quiz_context": None}


class AnsweringTests(unittest.TestCase):
    def test_answer_uses_only_retrieved_citation_metadata(self):
        result = AnswerService(Retriever(), Generator()).answer(answer_request())
        self.assertEqual(result["status"], "answered")
        self.assertEqual(result["retrieved_chunks"][0]["url"], "https://example.test/index")

    def test_missing_evidence_does_not_call_generator(self):
        generator = Generator(error=AssertionError("must not run"))
        result = AnswerService(Retriever([]), generator).answer(answer_request())
        self.assertEqual((result["status"], result["citations"] if "citations" in result else []),
                         ("insufficient_evidence", []))

    def test_unretrieved_or_missing_citation_is_rejected(self):
        for cited in ([], ["chunk:forged"]):
            generator = Generator({"status": "answered", "answer": "claim", "cited_chunk_ids": cited})
            with self.assertRaises(GenerationError):
                AnswerService(Retriever(), generator).answer(answer_request())

    def test_provider_failure_is_not_reported_as_insufficient_evidence(self):
        with self.assertRaises(GenerationError):
            AnswerService(Retriever(), Generator(error=OSError("down"))).answer(answer_request())

    def test_quiz_context_rewrites_ambiguous_question_and_evidence_is_untrusted(self):
        retriever, generator = Retriever(), Generator()
        request = answer_request()
        request["quiz_context"] = {"stem": "인덱스 단점은?", "options": [{"id": "a", "text": "쓰기 비용"}],
                                   "selected_option_id": "a", "correct_option_id": "a", "is_correct": True,
                                   "explanation": "유지 비용", "concept_ids": ["concept:database-index"]}
        request["question"] = "왜?"
        AnswerService(retriever, generator).answer(request)
        self.assertIn("인덱스 단점", retriever.last_question)
        self.assertIn("untrusted data", generator.system)
        self.assertIn("존댓말", generator.system)
        self.assertIn("even if the user", generator.system)
        self.assertIn("<evidence", generator.prompt)

    def test_internal_http_auth_validation_deadline_and_success(self):
        service = AnswerService(Retriever(), Generator())
        server = ThreadingHTTPServer(("127.0.0.1", 0), handler(service, "service-secret", "cs-test-v1"))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        url = f"http://127.0.0.1:{server.server_port}/internal/v1/answers"

        def call(data, token="service-secret"):
            request = Request(url, data=json.dumps(data).encode(), method="POST",
                              headers={"Content-Type": "application/json", "X-Request-Id": data["request_id"],
                                       "Authorization": "Bearer " + token})
            try:
                with urlopen(request) as response:
                    return response.status, json.load(response)
            except HTTPError as error:
                return error.code, json.load(error)

        try:
            self.assertEqual(call(answer_request())[0], 200)
            self.assertEqual(call(answer_request(), "wrong")[0], 401)
            wrong_index = {**answer_request(), "index_version": "old-v1"}
            self.assertEqual(call(wrong_index)[0], 409)
            expired = {**answer_request(), "deadline_at": "2020-01-01T00:00:00Z"}
            self.assertEqual(call(expired)[0], 504)
        finally:
            server.shutdown()
            server.server_close()

    def test_internal_health_endpoint_reports_active_index(self):
        service = AnswerService(Retriever(), Generator())
        server = ThreadingHTTPServer(("127.0.0.1", 0), handler(service, "service-secret", "cs-test-v1"))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with urlopen(f"http://127.0.0.1:{server.server_port}/health") as response:
                self.assertEqual(json.load(response), {"status": "UP", "index_version": "cs-test-v1"})
        finally:
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    unittest.main()
