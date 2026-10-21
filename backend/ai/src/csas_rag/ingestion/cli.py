"""Registry-based offline ingestion CLI."""
import argparse
import json
from pathlib import Path

from .config import load_registry, require_approved, PolicyError
from .parsing import digest
from .pipeline import collect
from .storage import Store


def main(argv=None) -> int:
    root = Path(__file__).resolve().parents[5]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("list", "collect"))
    parser.add_argument("--registry", type=Path, default=root / "docs/data-sources.json")
    parser.add_argument("--source", action="append")
    parser.add_argument("--priority", type=int, choices=range(4))
    parser.add_argument("--all", action="store_true", help="Include disabled source metadata in list")
    parser.add_argument("--max-documents", type=int)
    parser.add_argument("--sample", action="store_true", help="Limit each source to at most 3 documents")
    parser.add_argument("--dry-run", action="store_true", help="No network or filesystem writes")
    parser.add_argument("--retry-failed", action="store_true")
    parser.add_argument("--output", type=Path, default=root / "data/processed/ingestion")
    args = parser.parse_args(argv)
    if args.max_documents is not None and args.max_documents < 1:
        parser.error("--max-documents must be positive")
    try:
        sources = load_registry(args.registry)
    except (ValueError, KeyError, OSError) as error:
        parser.error(str(error))
    if args.source and set(args.source) - {s["id"] for s in sources}:
        parser.error("Unknown source id")
    sources = sorted((s for s in sources if (not args.source or s["id"] in args.source)
                      and (args.priority is None or s["priority"] == args.priority)), key=lambda s: (s["priority"], s["id"]))
    if args.command == "list":
        approved = []
        for s in sources:
            try:
                require_approved(s)
                approved.append(s)
            except PolicyError:
                if args.all:
                    approved.append(s)
        print(json.dumps(approved, ensure_ascii=False, indent=2))
        return 0
    limit = min(args.max_documents or 3, 3) if args.sample else args.max_documents
    # No catalog is created for dry-run or when no source can pass the gate.
    eligible = any(s["enabled"] for s in sources)
    store = Store(args.output) if eligible and not args.dry_run else None
    try:
        results = [collect(s, store, limit, args.dry_run, args.retry_failed) for s in sources]
        manifest = store.manifest(digest(args.registry.read_text(encoding="utf-8"))) if store else None
        report = {"sources": results, "corpus_digest": manifest["corpus_digest"] if manifest else None}
        print(json.dumps(report, ensure_ascii=False, indent=2))
        if store:
            (args.output / "last-run.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return 1 if any(r["failed"] for r in results) else 0
    finally:
        if store:
            store.close()
