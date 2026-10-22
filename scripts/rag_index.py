#!/usr/bin/env python3
"""Build a versioned Chroma index from an approved ingestion manifest."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend/ai/src"))

from csas_rag.indexing.pipeline import (activate_manifest, build_index, incremental_index,
                                        load_jsonl, write_manifest)
from csas_rag.providers.chroma import ChromaVectorStore
from csas_rag.providers.embeddings import DeterministicTestEmbedding, OpenAIEmbedding


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=ROOT / "data/processed/ingestion/normalized.jsonl")
    parser.add_argument("--ingestion-manifest", type=Path, default=ROOT / "data/processed/ingestion/manifest.json")
    parser.add_argument("--index-version", required=True)
    parser.add_argument("--provider", choices=("openai", "deterministic-test"), default="openai")
    parser.add_argument("--mode", choices=("full", "incremental"), default="full")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--complete-source", action="append", default=[],
                        help="Source whose uncapped discovery completed; absent documents may be deleted")
    parser.add_argument("--previous-manifest", type=Path,
                        help="Existing index manifest; defaults to the target manifest when present")
    parser.add_argument("--output", type=Path, default=ROOT / "data/processed/indexes")
    parser.add_argument("--activate-evaluation", type=Path,
                        help="JSON evaluation with passed=true and at least five queries")
    args = parser.parse_args(argv)
    ingestion = json.loads(args.ingestion_manifest.read_text(encoding="utf-8"))
    embedding = OpenAIEmbedding() if args.provider == "openai" else DeterministicTestEmbedding()
    path = args.output / (args.index_version + ".json")
    if args.mode == "incremental":
        previous_path = args.previous_manifest or path
        previous = (json.loads(previous_path.read_text(encoding="utf-8"))
                    if previous_path.exists() else None)
        manifest, stats = incremental_index(
            load_jsonl(args.input), ChromaVectorStore(args.index_version), embedding,
            args.index_version, ingestion["corpus_digest"], previous_manifest=previous,
            complete_source_ids=set(args.complete_source), dry_run=args.dry_run)
        print(json.dumps(stats, ensure_ascii=False, indent=2))
        if args.dry_run:
            return 0
    else:
        if args.dry_run:
            parser.error("--dry-run requires --mode incremental")
        manifest = build_index(load_jsonl(args.input), ChromaVectorStore(args.index_version), embedding,
                               args.index_version, ingestion["corpus_digest"])
    if args.activate_evaluation:
        evaluation = json.loads(args.activate_evaluation.read_text(encoding="utf-8"))
        manifest = activate_manifest(manifest, evaluation)
    write_manifest(path, manifest)
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    raise SystemExit(main())
