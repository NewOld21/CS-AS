#!/usr/bin/env python3
"""Common ingestion entry point; source policy stays in docs/data-sources.json."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend/ai/src"))
from csas_rag.ingestion.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
