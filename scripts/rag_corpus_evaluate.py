#!/usr/bin/env python3
"""Evaluate a live corpus index and promote its manifest only when all probes pass."""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend/ai/src"))

from csas_rag.indexing.pipeline import activate_manifest, write_manifest
from csas_rag.providers.chroma import ChromaVectorStore
from csas_rag.providers.embeddings import OpenAIEmbedding


PROBES = [
    ("운영 체제의 역할과 프로세스 관리를 설명해줘", {"gyoogle", "wikipedia-ko"}),
    ("자료 구조와 알고리즘의 차이는 무엇인가?", {"gyoogle", "wikipedia-ko"}),
    ("HTTP 메시지와 메서드의 의미를 설명해줘", {"rfc-editor", "mdn-http"}),
    ("HTTP 상태 코드와 요청 응답 의미를 알려줘", {"rfc-editor", "mdn-http"}),
    ("PostgreSQL MVCC와 트랜잭션 격리 수준을 설명해줘", {"postgresql"}),
]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--top-k", type=int, default=8)
    args = parser.parse_args(argv)
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    if manifest.get("status") != "BUILDING":
        raise SystemExit("Evaluation requires a BUILDING index manifest")
    embedding = OpenAIEmbedding(model=manifest["model"], dimensions=manifest["dimensions"])
    store = ChromaVectorStore(manifest["index_version"])
    rows = []
    for question, expected_sources in PROBES:
        results = store.query(embedding.embed([question])[0], args.top_k)
        found = {item["metadata"]["source_id"] for item in results}
        matched = sorted(found & expected_sources)
        rows.append({
            "question": question,
            "expected_sources": sorted(expected_sources),
            "matched_sources": matched,
            "passed": bool(matched),
            "top_sources": [item["metadata"]["source_id"] for item in results],
        })
    evaluation = {
        "passed": all(row["passed"] for row in rows),
        "query_count": len(rows),
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
        "index_version": manifest["index_version"],
        "results": rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(evaluation, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if evaluation["passed"]:
        write_manifest(args.manifest, activate_manifest(manifest, evaluation))
    print(json.dumps(evaluation, ensure_ascii=False, indent=2))
    return 0 if evaluation["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
