"""Document- and chunk-level retrieval metrics with auditable per-question evidence."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_TOP_KS = (1, 3, 5)
ALLOWED_CATEGORIES = {
    "operating-system",
    "network",
    "database",
    "data-structure-algorithm",
    "software-distributed-systems",
}


def load_dataset(path: Path) -> dict:
    dataset = json.loads(path.read_text(encoding="utf-8"))
    validate_dataset(dataset)
    return dataset


def validate_dataset(dataset: dict) -> None:
    if not isinstance(dataset, dict) or not dataset.get("version"):
        raise ValueError("Retrieval dataset requires a version")
    questions = dataset.get("questions")
    if not isinstance(questions, list) or not questions:
        raise ValueError("Retrieval dataset requires questions")
    identifiers = set()
    for row in questions:
        identifier = row.get("id")
        if not identifier or identifier in identifiers:
            raise ValueError("Question IDs must be non-empty and unique")
        identifiers.add(identifier)
        if row.get("category") not in ALLOWED_CATEGORIES:
            raise ValueError(f"Unsupported category for {identifier}")
        if not isinstance(row.get("question"), str) or not row["question"].strip():
            raise ValueError(f"Question text is required for {identifier}")
        evaluable = row.get("evaluable", True)
        documents = row.get("relevant_documents", [])
        if evaluable and not documents:
            raise ValueError(f"Evaluable question {identifier} needs relevant documents")
        if not evaluable and not row.get("insufficient_reason"):
            raise ValueError(f"Unevaluable question {identifier} needs a reason")
        seen_documents = set()
        for document in documents:
            document_id = document.get("document_id")
            if not isinstance(document_id, str) or not document_id.startswith("doc:"):
                raise ValueError(f"Invalid document ID for {identifier}")
            if document_id in seen_documents:
                raise ValueError(f"Duplicate relevant document for {identifier}")
            seen_documents.add(document_id)
            if not str(document.get("source_url", "")).startswith("https://"):
                raise ValueError(f"Relevant document URL is required for {identifier}")
        chunk_ids = row.get("relevant_chunk_ids", [])
        if not isinstance(chunk_ids, list) or any(not isinstance(value, str) for value in chunk_ids):
            raise ValueError(f"relevant_chunk_ids must be a string list for {identifier}")


def _ranked(rows: list[dict], key) -> list[str]:
    """Keep result positions: document metrics are measured at chunk result rank."""
    return [value for row in rows if (value := key(row))]


def _metric_block(results: list[dict], level: str, top_ks: tuple[int, ...]) -> dict:
    expected_key = f"relevant_{level}_ids"
    actual_key = f"retrieved_{level}_ids"
    eligible = [row for row in results if row[expected_key]]
    if not eligible:
        return {"evaluated_questions": 0, "status": "not_evaluated",
                "reason": f"dataset has no {level}-level relevance labels"}
    metrics = {"evaluated_questions": len(eligible), "status": "evaluated"}
    for top_k in top_ks:
        hits = []
        recalls = []
        for row in eligible:
            expected = set(row[expected_key])
            actual = set(row[actual_key][:top_k])
            hits.append(bool(expected & actual))
            recalls.append(len(expected & actual) / len(expected))
        metrics[f"hit_rate@{top_k}"] = sum(hits) / len(hits)
        metrics[f"recall@{top_k}"] = sum(recalls) / len(recalls)
    reciprocal_ranks = []
    for row in eligible:
        expected = set(row[expected_key])
        rank = next((index for index, value in enumerate(row[actual_key], 1) if value in expected), None)
        reciprocal_ranks.append(0.0 if rank is None else 1.0 / rank)
    metrics["mrr"] = sum(reciprocal_ranks) / len(reciprocal_ranks)
    return metrics


def evaluate_retrieval(dataset: dict, retriever, index_manifest: dict,
                       top_ks: tuple[int, ...] = DEFAULT_TOP_KS) -> dict:
    validate_dataset(dataset)
    if not top_ks or tuple(sorted(set(top_ks))) != top_ks or top_ks[0] < 1 or top_ks[-1] > 20:
        raise ValueError("top_ks must be sorted unique values from 1 to 20")
    results = []
    for question in dataset["questions"]:
        relevant_documents = [row["document_id"] for row in question.get("relevant_documents", [])]
        relevant_chunks = question.get("relevant_chunk_ids", [])
        if not question.get("evaluable", True):
            results.append({
                "id": question["id"], "category": question["category"],
                "question": question["question"], "status": "insufficient_evidence",
                "insufficient_reason": question["insufficient_reason"],
                "relevant_document_ids": relevant_documents, "relevant_chunk_ids": relevant_chunks,
                "retrieved_document_ids": [], "retrieved_chunk_ids": [], "retrieved": [],
                "missing_document_ids": relevant_documents, "missing_chunk_ids": relevant_chunks,
            })
            continue
        rows = retriever.search(question["question"], limit=top_ks[-1])
        document_ids = _ranked(rows, lambda row: row.get("metadata", {}).get("document_id"))
        chunk_ids = _ranked(rows, lambda row: row.get("chunk_id"))
        missing_documents = sorted(set(relevant_documents) - set(document_ids))
        missing_chunks = sorted(set(relevant_chunks) - set(chunk_ids))
        results.append({
            "id": question["id"], "category": question["category"],
            "question": question["question"], "status": "evaluated",
            "relevant_document_ids": relevant_documents, "relevant_chunk_ids": relevant_chunks,
            "retrieved_document_ids": document_ids, "retrieved_chunk_ids": chunk_ids,
            "retrieved": [{
                "rank": rank, "document_id": row.get("metadata", {}).get("document_id"),
                "chunk_id": row.get("chunk_id"), "title": row.get("metadata", {}).get("title"),
                "source_url": row.get("metadata", {}).get("url"),
                "score": row.get("score"), "distance": row.get("distance"),
            } for rank, row in enumerate(rows, 1)],
            "missing_document_ids": missing_documents,
            "missing_chunk_ids": missing_chunks,
            "failure_analysis": ({
                "code": "relevant_document_not_in_top_k",
                "details": "The labeled corpus document exists but no chunk from it appeared in the evaluated window. Review embedding rank, chunking, metadata, and filters.",
            } if missing_documents else ({
                "code": "relevant_chunk_not_in_top_k",
                "details": "The labeled document was found but the labeled chunk was outside the evaluated window; review chunking and embedding rank.",
            } if missing_chunks else None)),
        })
    evaluated = [row for row in results if row["status"] == "evaluated"]
    return {
        "schema_version": 1,
        "dataset_version": dataset["version"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "index": {
            key: index_manifest.get(key) for key in (
                "index_version", "collection", "model", "dimensions", "corpus_digest", "chunk_config"
            )
        },
        "top_ks": list(top_ks),
        "question_count": len(results),
        "evaluated_question_count": len(evaluated),
        "insufficient_evidence_count": len(results) - len(evaluated),
        "document_metrics": _metric_block(evaluated, "document", top_ks),
        "chunk_metrics": _metric_block(evaluated, "chunk", top_ks),
        "category_document_metrics": {
            category: _metric_block([row for row in evaluated if row["category"] == category],
                                    "document", top_ks)
            for category in sorted({row["category"] for row in evaluated})
        },
        "results": results,
    }
