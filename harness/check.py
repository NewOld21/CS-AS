#!/usr/bin/env python3
"""Validate the bootstrap configuration; not an application quality check."""
import argparse
import json
from pathlib import Path


def check(root):
    required = ['AGENTS.md', 'CLAUDE.md', '.clinerules/01-project.md', 'Harness.md',
                'docs/05_ARCHITECTURE.md', 'docs/api/openapi.yaml', 'docs/data-sources.json',
                'harness/README.md', 'harness/run.py', 'harness/evaluate.py',
                'harness/policy.json', 'harness/checks.json', 'harness/tasks/001-bootstrap.json',
                'harness/schemas/run-state.schema.json', 'harness/templates/handoff.md',
                'harness/evals/cases.jsonl', 'harness/evals/injection.jsonl']
    for name in required:
        if not (root / name).is_file():
            raise ValueError(f'Missing required file: {name}')
    for path in root.rglob('*.json'):
        if '.git' not in path.parts and 'node_modules' not in path.parts:
            json.loads(path.read_text(encoding='utf-8'))
    for name in ['AGENTS.md', 'CLAUDE.md', '.clinerules/01-project.md']:
        if 'Harness.md' not in (root / name).read_text(encoding='utf-8'):
            raise ValueError(f'Missing entry point reference: {name}')
    config = json.loads((root / 'harness/checks.json').read_text())
    for profile in ['bootstrap', 'full']:
        checks = config['profiles'][profile]
        if not checks or len({c['id'] for c in checks}) != len(checks):
            raise ValueError(f'Invalid checks: {profile}')
        for item in checks:
            if ('argv' in item) == ('pending' in item):
                raise ValueError('Each check must specify argv OR pending')
            if 'argv' in item and (not item['argv'] or not all(isinstance(x, str) for x in item['argv'])):
                raise ValueError('argv must be a nonempty string array')
    sources = json.loads((root / 'docs/data-sources.json').read_text())['sources']
    for source in sources:
        if source['enabled'] and source['usage_review'] != 'approved':
            raise ValueError('Enabled source must have approved usage review')
    cases = [json.loads(line) for line in (root / 'harness/evals/cases.jsonl').read_text().splitlines() if line]
    if len({c['id'] for c in cases}) != len(cases):
        raise ValueError('Duplicate evaluation cases')
    if sum(c['answerable'] for c in cases) < 20 or sum(not c['answerable'] for c in cases) < 5:
        raise ValueError('Need >=20 retrieval cases and >=5 abstention cases')
    return len(required)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path, default=Path(__file__).resolve().parent.parent)
    args = parser.parse_args()
    try:
        count = check(args.workspace.resolve())
    except (ValueError, KeyError, OSError) as error:
        print(f'FAIL: {error}')
        return 1
    print(f'PASS: bootstrap configuration ({count} required files); application not evaluated')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
