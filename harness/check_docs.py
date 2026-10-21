#!/usr/bin/env python3
"""Validate the documentation map and local Markdown links (no network)."""
import argparse
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit

REQUIRED = [
    'AGENTS.md', 'Harness.md', 'README.md',
    'backend/AGENTS.md', 'backend/ai/AGENTS.md', 'frontend/AGENTS.md', 'docs/AGENTS.md',
    'docs/README.md', 'docs/00_PROJECT_PROPOSAL.md', 'docs/01_PRD.md',
    'docs/02_MVP_SCOPE.md', 'docs/03_USER_FLOW.md', 'docs/04_SCREEN_SPEC.md',
    'docs/05_ARCHITECTURE.md', 'docs/06_ERD.md', 'docs/07_API_SPEC.md',
    'docs/08_AGENTS.md', 'docs/09_TEST_SCENARIO.md', 'docs/10_IMPLEMENTATION_PLAN.md',
    'docs/11_TEAM_OWNERSHIP.md', 'docs/12_GIT_CONVENTION.md',
    'docs/13_PHASE0_DECISIONS.md', 'docs/14_RAG_GUIDE.md', 'docs/development.md',
    'docs/current-task.md', 'docs/domain/ingestion.md', 'docs/domain/retrieval.md',
    'docs/domain/answering.md', 'docs/api/openapi.yaml',
    'docs/decisions/README.md', 'docs/runbooks/README.md', 'docs/exec-plans/README.md',
    'docs/exec-plans/completed/README.md',
    'scripts/README.md', 'scripts/verify.py', 'scripts/task.py', 'scripts/check_docs.py',
]
EXCLUDED = {'.git', '.venv', 'node_modules', '__pycache__', '.harness-state'}


def check(root):
    root = root.resolve()
    errors = [f'Missing required document: {name}' for name in REQUIRED if not (root / name).is_file()]
    count = 0
    for path in sorted(root.rglob('*.md')):
        if EXCLUDED.intersection(path.relative_to(root).parts):
            continue
        content = re.sub(r'```.*?```', '', path.read_text(encoding='utf-8'), flags=re.S)
        for destination in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)', content):
            destination = destination.strip().split(' "', 1)[0].strip('<>')
            url = urlsplit(destination)
            if url.scheme or url.netloc or not url.path:
                continue
            target = (path.parent / unquote(url.path)).resolve()
            count += 1
            if not target.is_relative_to(root) or not target.exists():
                errors.append(f'{path.relative_to(root)}: broken local link {destination}')
    for scope in ['backend', 'backend/ai', 'frontend', 'docs']:
        file = root / scope / 'AGENTS.md'
        if file.is_file() and '08_AGENTS.md' not in file.read_text(encoding='utf-8'):
            errors.append(f'{scope}/AGENTS.md must reference shared guide')
    return errors, count


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path, default=Path(__file__).resolve().parent.parent)
    args = parser.parse_args()
    errors, count = check(args.workspace)
    if errors:
        print('\n'.join(errors))
        return 1
    print(f'PASS: documentation structure and {count} local links (URL/anchor content not evaluated)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
