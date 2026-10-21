"""Reproducible synthetic four-source sample; does not access the network."""
import argparse
import json
from pathlib import Path

from support import fixture_factory, fixture_source
from csas_rag.ingestion.parsing import digest
from csas_rag.ingestion.pipeline import collect
from csas_rag.ingestion.storage import Store


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    sources = [fixture_source("github"), fixture_source("mediawiki", "ko"),
               fixture_source("mediawiki", "en"), fixture_source()]
    store = Store(args.output)
    try:
        report = {"synthetic": True,
                  "first_run": [collect(s, store, limit=1, factory=fixture_factory) for s in sources],
                  "repeat_run": [collect(s, store, limit=1, factory=fixture_factory) for s in sources]}
        report["corpus_digest"] = store.manifest(digest(json.dumps(sources, sort_keys=True)))["corpus_digest"]
        path = args.output / "sample-report.json"
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return int(any(r["failed"] or r["excluded_policy"] or r["excluded_sources"]
                       for key in ("first_run", "repeat_run") for r in report[key]))
    finally:
        store.close()


if __name__ == "__main__":
    raise SystemExit(main())
