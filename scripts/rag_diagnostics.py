#!/usr/bin/env python3
"""Run bounded live diagnostics for registry, GMS, Chroma, retrieval, and RAG."""
import argparse
import json
import os
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend/ai/src"))

from csas_rag.generation.answering import AnswerService
from csas_rag.providers.chroma import ChromaVectorStore
from csas_rag.providers.embeddings import OpenAIEmbedding
from csas_rag.providers.llm import OpenAIAnswerGenerator
from csas_rag.retrieval.vector import VectorRetriever


QUESTIONS = [
    "프로세스와 스레드의 차이는?",
    "TCP와 UDP의 차이는?",
    "데이터베이스 트랜잭션이란?",
    "데드락이 발생하는 조건은?",
    "데이터베이스 인덱스는 왜 사용하는가?",
]

EXPECTED_TITLES = [
    {"POSIX threads"},
    {"TCP", "UDP"},
    {"PostgreSQL transactions"},
    {"Deadlock"},
    {"PostgreSQL index types"},
]


def check(status: str, **details) -> dict:
    return {"status": status, **details}


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def registry_diagnostic() -> dict:
    registry = json.loads((ROOT / "docs/data-sources.json").read_text(encoding="utf-8"))
    sources = registry["sources"]
    by_kind = Counter(source["kind"] for source in sources)
    approved = [source for source in sources if source.get("enabled") is True
                and source.get("usage_review") == "approved"]
    return check("PASS", total=len(sources), approved_enabled=len(approved),
                 by_kind=dict(sorted(by_kind.items())), ossu_present=any("ossu" in source["id"].lower()
                 for source in sources))


def corpus_diagnostic() -> dict:
    directory = ROOT / "data/processed/ingestion"
    normalized = load_jsonl(directory / "normalized.jsonl")
    chunks = load_jsonl(directory / "chunks.jsonl")
    if not normalized and not chunks:
        return check("SKIP", reason="No approved live corpus has been collected", documents=0, chunks=0,
                     path=str(directory))
    required = ("source_id", "document_id", "revision", "source_url", "title", "content")
    missing = sum(any(not row.get(field) for field in required) for row in normalized)
    empty_chunks = sum(not row.get("content", row.get("text", "")).strip() for row in chunks)
    duplicate_documents = len(normalized) - len({(row.get("document_id"), row.get("revision"))
                                                  for row in normalized})
    duplicate_chunks = len(chunks) - len({row.get("chunk_id") for row in chunks})
    status = "PASS" if not any((missing, empty_chunks, duplicate_documents, duplicate_chunks)) else "FAIL"
    return check(status, documents=len(normalized), chunks=len(chunks), missing_required=missing,
                 empty_chunks=empty_chunks, duplicate_documents=duplicate_documents,
                 duplicate_chunks=duplicate_chunks, by_source=dict(Counter(
                     row.get("source_id", "unknown") for row in normalized)))


def live_diagnostic(index_version: str) -> dict:
    embedding = OpenAIEmbedding()
    vectors = embedding.embed(QUESTIONS)
    dimension = len(vectors[0])
    store = ChromaVectorStore(index_version)
    manifest = {"model": embedding.model, "dimensions": embedding.dimensions}
    retriever = VectorRetriever(store, embedding, manifest)
    searches = []
    relevant_count = 0
    for question, vector, expected in zip(QUESTIONS, vectors, EXPECTED_TITLES):
        rows = store.query(vector, 3)
        titles = {row["metadata"]["title"] for row in rows}
        relevant = expected <= titles
        relevant_count += int(relevant)
        searches.append({
            "question": question,
            "count": len(rows),
            "expected_titles": sorted(expected),
            "relevant": relevant,
            "top": [{"title": row["metadata"]["title"], "url": row["metadata"]["url"],
                     "score": round(row["score"], 6), "chunk_id": row["chunk_id"]} for row in rows],
        })
    request = {
        "request_id": "gms-live-diagnostic",
        "deadline_at": (datetime.now(timezone.utc) + timedelta(minutes=2)).isoformat(),
        "index_version": index_version,
        "question": "프로세스와 스레드의 차이를 설명하고 각각의 장단점을 예시와 함께 알려줘.",
        "history": [],
        "quiz_context": None,
    }
    service = AnswerService(retriever, OpenAIAnswerGenerator(), min_score=-1.0)
    answer = service.answer(request)
    retrieved = {row["chunk_id"] for row in answer["retrieved_chunks"]}
    citations_valid = bool(answer["cited_chunk_ids"]) and set(answer["cited_chunk_ids"]) <= retrieved
    insufficient_request = {**request, "request_id": "gms-live-insufficient", "question": "근거 없는 질문",
                            "quiz_context": {"stem": "없는 개념", "options": [{"id": "a", "text": "없음"}],
                            "selected_option_id": "a", "correct_option_id": "a", "is_correct": True,
                            "explanation": "없음", "concept_ids": ["concept:not-in-local-index"]}}
    insufficient = service.answer(insufficient_request)
    return {
        "gms_embedding": check("PASS", model=embedding.model, dimensions=dimension,
                               batch_inputs=len(QUESTIONS)),
        "chroma": check("PASS", collection=store.name, chunks=store.count()),
        "vector_search": check("PASS" if all(row["count"] for row in searches) else "FAIL",
                               queries=searches),
        "retrieval_relevance": check("PASS" if relevant_count == len(searches) else "FAIL",
                                     relevant_queries=relevant_count, total_queries=len(searches)),
        "gms_chat": check("PASS" if answer["status"] == "answered" else "FAIL",
                          model=answer["model_version"]),
        "rag_answer": check("PASS" if answer["status"] == "answered" else "FAIL",
                            answer=answer["answer"], sources=answer["retrieved_chunks"]),
        "citation_validation": check("PASS" if citations_valid else "FAIL",
                                     cited_chunk_ids=answer["cited_chunk_ids"]),
        "insufficient_evidence": check("PASS" if insufficient["status"] == "insufficient_evidence"
                                       else "FAIL"),
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index-version", default=os.environ.get("RAG_ACTIVE_INDEX", "gms-live-dev-v1"))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": "live-gms-local-fixture",
        "source_registry": registry_diagnostic(),
        "corpus": corpus_diagnostic(),
    }
    try:
        result.update(live_diagnostic(args.index_version))
    except Exception as error:
        result["live_pipeline"] = check("FAIL", error_type=type(error).__name__)
    rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 1 if any(value.get("status") == "FAIL" for value in result.values()
                    if isinstance(value, dict)) else 0


if __name__ == "__main__":
    raise SystemExit(main())
