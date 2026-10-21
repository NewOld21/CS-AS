#!/usr/bin/env python3
"""Public entry point for the existing harness state/verification engine."""
from pathlib import Path
import runpy

if __name__ == '__main__':
    runpy.run_path(str(Path(__file__).resolve().parents[1] / 'harness/run.py'), run_name='__main__')
