#!/usr/bin/env python3
"""Common repository verification entry point. Bootstrap is not app completion."""
import argparse
from pathlib import Path
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', choices=['bootstrap', 'full'], default='bootstrap')
    parser.add_argument('--state-dir', type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    if args.profile == 'full':
        if args.state_dir is None:
            parser.error('full requires --state-dir initialized with scripts/task.py init')
        commands = [[sys.executable, str(root / 'harness/run.py'), 'verify', '--workspace', str(root),
                     '--state-dir', str(args.state_dir.resolve()), '--profile', 'full']]
    else:
        commands = [
            [sys.executable, str(root / 'harness/check_docs.py')],
            [sys.executable, str(root / 'harness/check.py')],
            [sys.executable, '-m', 'unittest', 'discover', '-s', str(root / 'harness/tests'), '-v'],
        ]
    failures = 0
    for command in commands:
        result = subprocess.run(command, cwd=root, check=False)
        failures += result.returncode != 0
    return 1 if failures else 0


if __name__ == '__main__':
    raise SystemExit(main())
