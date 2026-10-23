import copy
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from csas_rag.generation.answering import GenerationError
from csas_rag.generation.quiz import QuizService, validate_quiz_request
from csas_rag.generation.quiz.validation import validate_candidate


def request():
    return {"request_id": "generation-1", "index_version": "test-v1",
            "deadline_at": (datetime.now(timezone.utc) + timedelta(seconds=60)).isoformat(),
            "concept_ids": ["concept:database-index"], "concept_labels": ["Database index"],
            "difficulty": "EASY", "learning_context": "Index maintenance costs"}


def candidate():
    return {"stem": "Which statement about indexes is correct?",
            "options": [{"position": i + 1, "text": t} for i, t in enumerate([
                "Indexes require maintenance on writes", "Indexes have no storage cost",
                "Indexes always speed up every write", "Indexes replace all tables"])],
            "correct_option_position": 1, "explanation": "Indexes incur maintenance costs on writes.",
            "difficulty": "EASY", "concept_ids": ["concept:database-index"], "evidence_chunk_ids": ["chunk:1"]}


class Retriever:
    manifest = {"corpus_digest": "fixture-digest"}
    def search(self, query, limit, concepts):
        self.query, self.concepts = query, concepts
        return [{"chunk_id": "chunk:1", "content": "Indexes require storage and incur maintenance costs on writes.",
                 "score": 0.9, "metadata": {"source_id": "fixture", "document_id": "doc:1", "revision": "1",
                                          "title": "Indexes", "url": "https://example.org/index", "locator": "section:1"}}]


class Generator:
    model = "gms-mock"
    def __init__(self, responses=None):
        self.responses = list(responses if responses is not None else [candidate()])
        self.calls = []
    def generate(self, system, prompt):
        self.calls.append((system, prompt))
        value = self.responses.pop(0)
        if isinstance(value, Exception):
            raise value
        return copy.deepcopy(value)


class QuizGenerationTests(unittest.TestCase):
    def test_candidate_is_never_published_without_validator(self):
        retriever, generator = Retriever(), Generator()
        result = QuizService(retriever, generator).generate(request())
        self.assertEqual(result["reason_codes"], ["VALIDATION_NOT_CONFIGURED"])
        self.assertIsNone(result["candidate"])
        self.assertIn("Index maintenance", retriever.query)
        self.assertIn("chunk:1", generator.calls[0][1])
        self.assertEqual(result["corpus_digest"], "fixture-digest")

    def test_empty_evidence_does_not_call_gms(self):
        retriever = Retriever()
        retriever.search = lambda *args: []
        generator = Generator()
        self.assertEqual(QuizService(retriever, generator).generate(request())["status"], "insufficient_evidence")
        self.assertEqual(generator.calls, [])

    def test_provider_failure_is_not_insufficient_evidence(self):
        with self.assertRaises(GenerationError):
            QuizService(Retriever(), Generator([ValueError("bad JSON")])).generate(request())

    def test_invalid_concepts_and_expired_deadline(self):
        for concepts in ([], ["invented"], ["concept:x", "concept:x"]):
            with self.assertRaises(ValueError):
                validate_quiz_request({**request(), "concept_ids": concepts})
        with self.assertRaises(TimeoutError):
            QuizService(Retriever(), Generator()).generate({**request(), "deadline_at": "2020-01-01T00:00:00Z"})


def blind(**changes):
    return {"correct_positions": [1], "ambiguous": False, "supported": True,
            "concept_match": True, "evidence_chunk_ids": ["chunk:1"], **changes}


def audit(**changes):
    return {"explanation_supported": True, "distractors_incorrect": True,
            "version_unambiguous": True, "no_answer_leak": True, "not_copied": True,
            "evidence_chunk_ids": ["chunk:1"], **changes}


class QuizValidationTests(unittest.TestCase):
    def run_candidate(self, value, solving=None, auditing=None):
        generator = Generator([value, solving if solving is not None else blind(),
                               auditing if auditing is not None else audit()])
        return QuizService(Retriever(), generator, validate_candidate).generate(request()), generator

    def test_valid_candidate_requires_three_independent_stages(self):
        result, generator = self.run_candidate(candidate())
        self.assertEqual(result["status"], "validated")
        self.assertEqual(len(generator.calls), 3)
        blind_prompt = generator.calls[1][1]
        self.assertNotIn('"correct_option_position"', blind_prompt)
        self.assertNotIn('"explanation"', blind_prompt)
        self.assertTrue(all(r["passed"] for r in result["validation_report"]))

    def test_invalid_schema_options_and_types_never_reach_semantic_calls(self):
        cases = []
        for size in (3, 5):
            c = candidate(); c["options"] = (c["options"] * 2)[:size]; cases.append(c)
        c = candidate(); del c["correct_option_position"]; cases.append(c)
        for changes in ({"correct_option_position": 0}, {"correct_option_position": True},
                        {"explanation": ""}, {"stem": ""}, {"difficulty": "INVALID"},
                        {"user_id": "injected"}, {"concept_ids": ["concept:invented"]},
                        {"evidence_chunk_ids": ["invented"]}):
            cases.append({**candidate(), **changes})
        c = candidate(); c["options"][1]["text"] = c["options"][0]["text"].upper() + "!"; cases.append(c)
        c = candidate(); c["options"][1]["position"] = 1; cases.append(c)
        for value in cases:
            with self.subTest(value=value):
                result, generator = self.run_candidate(value)
                self.assertEqual(result["status"], "validation_failed")
                self.assertIsNone(result["candidate"])
                self.assertEqual(len(generator.calls), 1)

    def test_multiple_no_wrong_and_ambiguous_answers_rejected(self):
        for solving in (blind(correct_positions=[1, 2]), blind(correct_positions=[]),
                        blind(correct_positions=[2]), blind(ambiguous=True), blind(supported=False),
                        blind(concept_match=False), blind(evidence_chunk_ids=["invented"]), {}):
            with self.subTest(solving=solving):
                result, _ = self.run_candidate(candidate(), solving=solving)
                self.assertEqual(result["status"], "validation_failed")
                self.assertIsNone(result["candidate"])

    def test_unsupported_explanation_duplicate_meaning_and_versions_rejected(self):
        for field in ("explanation_supported", "distractors_incorrect", "version_unambiguous", "no_answer_leak", "not_copied"):
            with self.subTest(field=field):
                result, _ = self.run_candidate(candidate(), auditing=audit(**{field: False}))
                self.assertEqual(result["status"], "validation_failed")
                self.assertIsNone(result["candidate"])

    def test_validation_provider_failure_is_system_failure(self):
        with self.assertRaises(GenerationError):
            self.run_candidate(candidate(), solving=RuntimeError("provider failed"))
