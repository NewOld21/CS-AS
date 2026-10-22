#!/usr/bin/env python3
"""Evaluate an existing Chroma index against the versioned CS retrieval dataset."""
import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend/ai/src"))

from csas_rag.evaluation.retrieval import evaluate_retrieval, load_dataset
from csas_rag.providers.chroma import ChromaVectorStore
from csas_rag.providers.embeddings import OpenAIEmbedding
from csas_rag.retrieval.vector import VectorRetriever


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=ROOT / "harness/evals/retrieval-v1.json")
    parser.add_argument("--index-version", default=os.environ.get("RAG_ACTIVE_INDEX"))
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--output", type=Path, default=ROOT / "reports/retrieval-evaluation.json")
    args = parser.parse_args(argv)
    if not args.index_version:
        parser.error("--index-version or RAG_ACTIVE_INDEX is required")
    manifest_path = args.manifest or ROOT / "data/processed/indexes" / f"{args.index_version}.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("index_version") != args.index_version:
        parser.error("manifest index_version does not match --index-version")
    embedding = OpenAIEmbedding(model=manifest["model"], dimensions=manifest["dimensions"])
    retriever = VectorRetriever(ChromaVectorStore(args.index_version), embedding, manifest)
    report = evaluate_retrieval(load_dataset(args.dataset), retriever, manifest)
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
