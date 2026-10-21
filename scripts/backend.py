#!/usr/bin/env python3
"""Run the Java backend or its isolated PostgreSQL integration checks from the root."""
import argparse
from pathlib import Path
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['check', 'up'])
    parser.add_argument('--docker-config', type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    command = ['docker']
    if args.docker_config:
        command += ['--config', str(args.docker_config.resolve())]
    command += ['compose']
    if args.action == 'up':
        command += ['-f', 'compose.yaml', '-f', 'compose.backend.yaml', 'up', '-d', 'backend']
        return subprocess.call(command, cwd=root)
    command += ['-f', 'compose.backend-test.yaml']
    subprocess.run(command + ['up', '-d', '--wait', 'postgres-test'], cwd=root, check=True)
    return subprocess.call(command + ['run', '--rm', 'checks'], cwd=root)


if __name__ == '__main__':
    raise SystemExit(main())
