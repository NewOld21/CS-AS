#!/usr/bin/env python3
"""Run the Vue frontend or its locked local checks."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['dev', 'check', 'e2e'])
    args = parser.parse_args()
    npm = shutil.which('npm.cmd' if os.name == 'nt' else 'npm')
    if not npm:
        parser.error('Node.js and npm are required; see docs/development.md')
    directory = Path(__file__).resolve().parents[1] / 'frontend'
    commands = ['format:check', 'typecheck', 'lint', 'test', 'build'] if args.action == 'check' else ['test:e2e' if args.action == 'e2e' else 'dev']
    for command in commands:
        subprocess.run([npm, 'run', command], cwd=directory, check=True)


if __name__ == '__main__':
    main()
