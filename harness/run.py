#!/usr/bin/env python3
"""POSIX verification supervisor helper. Not a security sandbox or LLM agent."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from contextlib import contextmanager

HARNESS = Path(__file__).resolve().parent
EXCLUDED = {'.git', '.venv', 'node_modules', '__pycache__', '.harness-state',
            'state', 'reports', 'build', 'dist', '.gradle', '.pytest_cache',
            '.mypy_cache', '.ruff_cache', 'data'}


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def atomic_json(path, value):
    path = Path(path)
    temporary = path.with_suffix('.tmp')
    with temporary.open('w', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)


def digest_workspace(workspace):
    digest = hashlib.sha256()
    for parent, directories, names in os.walk(workspace, followlinks=False):
        for name in sorted(directories):
            path = Path(parent) / name
            if name not in EXCLUDED and path.is_symlink():
                digest.update(path.relative_to(workspace).as_posix().encode() + b'\0link:')
                digest.update(os.readlink(path).encode() + b'\0')
        directories[:] = sorted(d for d in directories if d not in EXCLUDED
                                and not (Path(parent) / d).is_symlink())
        for name in sorted(names):
            path = Path(parent) / name
            if name.startswith('.env') or path.suffix in {'.pem', '.key', '.pyc', '.patch'}:
                continue
            relative = path.relative_to(workspace).as_posix()
            digest.update(relative.encode() + b'\0')
            if path.is_symlink():
                digest.update(b'link:' + os.readlink(path).encode())
            else:
                digest.update(path.read_bytes())
            digest.update(b'\0')
    return digest.hexdigest()


def event(directory, name, **fields):
    with (directory / 'events.jsonl').open('a', encoding='utf-8') as stream:
        stream.write(json.dumps({'time': time.time(), 'event': name, **fields},
                                ensure_ascii=False) + '\n')
        stream.flush()
        os.fsync(stream.fileno())


@contextmanager
def locked(directory):
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    with (directory / '.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        yield


def execute(argv, cwd, timeout):
    """Discard raw output; never load child-controlled reports as instructions."""
    try:
        process = subprocess.Popen(argv, cwd=cwd, stdin=subprocess.DEVNULL,
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                   start_new_session=True)
    except (OSError, ValueError):
        return {'status': 'unavailable', 'exit_code': None}
    try:
        code = process.wait(timeout=timeout)
        return {'status': 'passed' if code == 0 else 'failed', 'exit_code': code}
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait()
        return {'status': 'timeout', 'exit_code': None}
    finally:
        # Also reap any descendants left behind after the parent exits.
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass


def write_handoff(directory, state):
    # Keep free-form human/agent notes in a separate file; do not overwrite them.
    lines = ['# 실행 상태 인계', '', f"- task: {state['task_id']}",
             f"- 상태: {state['status']}",
             f"- 프로파일: {state.get('profile', '미실행')}",
             f"- 검증 시도: {state['attempts']}",
             f"- 후보 digest: {state.get('candidate_digest', '미기록')}",
             f"- 중단 사유: {state.get('blocker') or '없음'}", '', '## 검사 결과', '']
    for result in state.get('checks', []):
        lines.append(f"- {result['id']}: {result['status']}")
    lines += ['', '## 이어서 할 일', '',
              '- reports/의 검증 증거와 task 완료 조건을 확인한다.',
              '- 원인 가설·시도·다음 행동은 notes.md에 추가한다.',
              '- 외부 관리자가 보존한 patch와 미추적 파일 snapshot을 확인한다.',
              '- blocked 상태에서는 예산을 초기화하지 말고 인간에게 인계한다.', '']
    (directory / 'handoff.md').write_text('\n'.join(lines), encoding='utf-8')


def persist(directory, state):
    state['updated_at'] = time.time()
    atomic_json(directory / 'state.json', state)
    write_handoff(directory, state)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['init', 'verify', 'handoff'])
    parser.add_argument('--workspace', type=Path, default=HARNESS.parent)
    parser.add_argument('--state-dir', type=Path, required=True)
    parser.add_argument('--task', type=Path)
    parser.add_argument('--profile', choices=['bootstrap', 'full'], default='full')
    args = parser.parse_args(argv)
    workspace = args.workspace.resolve()
    directory = args.state_dir.resolve()
    if not workspace.is_dir() or directory.is_relative_to(workspace):
        parser.error('workspace must exist; state-dir must be outside workspace')
    policy_bytes = (HARNESS / 'policy.json').read_bytes()
    config_bytes = (HARNESS / 'checks.json').read_bytes()
    policy = json.loads(policy_bytes)
    # Bind executable policy/checker code as well as declarative configuration.
    trusted_digest = digest_workspace(HARNESS)
    limits = policy['limits']
    with locked(directory):
        state_path = directory / 'state.json'
        if args.action == 'init':
            if state_path.exists():
                parser.error('state already exists; resume or hand off, do not reset')
            if args.task is None:
                parser.error('--task is required for init')
            task = read_json(args.task)
            if not task.get('id') or not task.get('acceptance_criteria'):
                parser.error('task requires id and nonempty acceptance_criteria')
            state = {'schema_version': 1, 'task_id': task['id'], 'status': 'initialized',
                     'started_at': time.time(), 'attempts': 0, 'same_failure_count': 0,
                     'last_failure': None, 'workspace': str(workspace),
                     'trusted_digest': trusted_digest, 'blocker': None, 'checks': []}
            atomic_json(directory / 'task.json', task)
            persist(directory, state)
            event(directory, 'initialized', task_id=task['id'])
            print(f'Initialized {task["id"]}; state: {directory}')
            return 0
        if not state_path.exists():
            parser.error('init must run first')
        state = read_json(state_path)
        if args.action == 'handoff':
            write_handoff(directory, state)
            print(directory / 'handoff.md')
            return 0
        blocker = None
        if state['status'] == 'blocked':
            blocker = state['blocker']
        elif state['status'] == 'running':
            blocker = 'INTERRUPTED_PREVIOUS_VERIFICATION'
        elif state['workspace'] != str(workspace):
            blocker = 'WORKSPACE_CHANGED'
        elif state['trusted_digest'] != trusted_digest:
            blocker = 'TRUSTED_POLICY_CHANGED'
        elif state['attempts'] >= limits['max_verification_attempts']:
            blocker = 'ATTEMPTS_EXHAUSTED'
        elif time.time() - state['started_at'] >= limits['max_task_seconds']:
            blocker = 'TASK_DEADLINE_EXCEEDED'
        if blocker:
            state.update(status='blocked', blocker=blocker)
            persist(directory, state)
            event(directory, 'blocked', reason=blocker)
            print(f'BLOCKED: {blocker}')
            return 2
        state.update(status='running', blocker=None, profile=args.profile,
                     attempts=state['attempts'] + 1, checks=[],
                     candidate_digest=digest_workspace(workspace))
        persist(directory, state)
        event(directory, 'verification_started', attempt=state['attempts'], profile=args.profile)
        checks = json.loads(config_bytes)['profiles'][args.profile]
        for check in checks:
            remaining = limits['max_task_seconds'] - (time.time() - state['started_at'])
            if remaining <= 0:
                result = {'status': 'timeout', 'exit_code': None}
            elif 'pending' in check:
                result = {'status': 'pending', 'exit_code': None}
            else:
                cwd = (workspace / check.get('cwd', '.')).resolve()
                if not cwd.is_relative_to(workspace) or not cwd.is_dir():
                    result = {'status': 'unavailable', 'exit_code': None}
                else:
                    command = [part.replace('{harness}', str(HARNESS))
                               .replace('{workspace}', str(workspace)) for part in check['argv']]
                    result = execute(command, cwd, min(remaining, limits['command_timeout_seconds']))
            state['checks'].append({'id': check['id'], **result})
            event(directory, 'check_finished', **state['checks'][-1])
            persist(directory, state)
        failed = [r for r in state['checks'] if r['status'] != 'passed']
        if digest_workspace(workspace) != state['candidate_digest']:
            failed.append({'id': 'candidate-changed-during-check', 'status': 'failed', 'exit_code': None})
            state['checks'] = state['checks'] + [failed[-1]]
        if failed:
            fingerprint = hashlib.sha256(json.dumps(failed, sort_keys=True).encode()).hexdigest()
            state['same_failure_count'] = (state['same_failure_count'] + 1
                                           if fingerprint == state['last_failure'] else 1)
            state['last_failure'] = fingerprint
            state['status'] = 'failed'
            if state['same_failure_count'] >= limits['same_failure_limit']:
                state.update(status='blocked', blocker='REPEATED_FAILURE')
            elif state['attempts'] >= limits['max_verification_attempts']:
                state.update(status='blocked', blocker='ATTEMPTS_EXHAUSTED')
        else:
            state.update(status='checks_passed', last_failure=None, same_failure_count=0)
        if time.time() - state['started_at'] >= limits['max_task_seconds']:
            state.update(status='blocked', blocker='TASK_DEADLINE_EXCEEDED')
        (directory / 'reports').mkdir(exist_ok=True)
        atomic_json(directory / 'reports' / f"attempt-{state['attempts']}.json", state)
        persist(directory, state)
        event(directory, 'verification_finished', status=state['status'])
        print(f"{args.profile}: {state['status']} ({len(failed)} failed/pending)")
        # checks_passed is deliberately not task-completed.
        return 0 if state['status'] == 'checks_passed' else 1


if __name__ == '__main__':
    sys.exit(main())
