import copy
import importlib.util
import json
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

H = Path(__file__).resolve().parents[1]
ROOT = H.parent


def module(name):
    spec = importlib.util.spec_from_file_location('csas_' + name, H / f'{name}.py')
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


runner = module('run')
evaluator = module('evaluate')
checker = module('check')


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.directory = Path(self.temp.name) / 'state'
        self.workspace = Path(self.temp.name) / 'workspace'
        self.workspace.mkdir()
        self.args = ['--workspace', str(self.workspace), '--state-dir', str(self.directory)]
        runner.main(['init', *self.args, '--task', str(H / 'tasks/001-bootstrap.json')])

    def tearDown(self):
        self.temp.cleanup()

    def state(self):
        return runner.read_json(self.directory / 'state.json')

    def test_repeated_failure_persists_and_blocks(self):
        for expected in ['failed', 'blocked']:
            with patch.object(runner, 'execute', return_value={'status': 'failed', 'exit_code': 1}):
                # full includes pending checks even when commands cannot run.
                self.assertEqual(runner.main(['verify', *self.args, '--profile', 'full']), 1)
            self.assertEqual(self.state()['status'], expected)
        self.assertEqual(self.state()['attempts'], 2)
        self.assertEqual(runner.main(['verify', *self.args]), 2)
        self.assertEqual(self.state()['attempts'], 2)

    def test_existing_state_cannot_be_reset(self):
        with self.assertRaises(SystemExit):
            runner.main(['init', *self.args, '--task', str(H / 'tasks/001-bootstrap.json')])
        self.assertEqual(self.state()['attempts'], 0)

    def test_deadline_survives_resume(self):
        state = self.state()
        state['started_at'] = time.time() - 1801
        runner.atomic_json(self.directory / 'state.json', state)
        self.assertEqual(runner.main(['verify', *self.args]), 2)
        self.assertEqual(self.state()['blocker'], 'TASK_DEADLINE_EXCEEDED')

    def test_interrupted_verification_requires_handoff(self):
        state = self.state()
        state['status'] = 'running'
        runner.atomic_json(self.directory / 'state.json', state)
        self.assertEqual(runner.main(['verify', *self.args]), 2)
        self.assertEqual(self.state()['blocker'], 'INTERRUPTED_PREVIOUS_VERIFICATION')

    def test_state_inside_workspace_is_rejected(self):
        with self.assertRaises(SystemExit):
            runner.main(['init', '--state-dir', str(self.workspace / 'state'),
                         '--workspace', str(self.workspace), '--task', str(H / 'tasks/001-bootstrap.json')])

    def test_process_timeout(self):
        result = runner.execute([sys.executable, '-c', 'import time; time.sleep(10)'], self.workspace, 0.05)
        self.assertEqual(result['status'], 'timeout')

    def test_digest_tracks_untracked_files_and_ignores_generated_cache(self):
        before = runner.digest_workspace(self.workspace)
        (self.workspace / 'new.py').write_text('print(1)')
        changed = runner.digest_workspace(self.workspace)
        self.assertNotEqual(before, changed)
        (self.workspace / '__pycache__').mkdir()
        (self.workspace / '__pycache__/ignored').write_text('generated')
        self.assertEqual(changed, runner.digest_workspace(self.workspace))

    def test_handoff_preserves_notes(self):
        (self.directory / 'notes.md').write_text('next hypothesis')
        runner.main(['handoff', *self.args])
        self.assertEqual((self.directory / 'notes.md').read_text(), 'next hypothesis')

    def test_attempt_budget_is_enforced(self):
        state = self.state()
        state['attempts'] = 4
        runner.atomic_json(self.directory / 'state.json', state)
        self.assertEqual(runner.main(['verify', *self.args]), 2)
        self.assertEqual(self.state()['blocker'], 'ATTEMPTS_EXHAUSTED')

    def test_bootstrap_pass_is_not_task_completion(self):
        with patch.object(runner, 'execute', return_value={'status': 'passed', 'exit_code': 0}):
            self.assertEqual(runner.main(['verify', *self.args, '--profile', 'bootstrap']), 0)
        self.assertEqual(self.state()['status'], 'checks_passed')


class EvaluationTests(unittest.TestCase):
    def setUp(self):
        self.cases = [
            {'id': 'known', 'ready': True, 'answerable': True, 'relevant_document_ids': ['doc']},
            {'id': 'unknown', 'ready': True, 'answerable': False, 'relevant_document_ids': []}]
        self.predictions = [
            {'id': 'known', 'status': 'answered', 'retrieved_document_ids': ['doc'],
             'retrieved_chunk_ids': ['chunk'], 'cited_chunk_ids': ['chunk']},
            {'id': 'unknown', 'status': 'insufficient_evidence', 'retrieved_document_ids': [],
             'retrieved_chunk_ids': [], 'cited_chunk_ids': []}]

    def test_valid_results_pass(self):
        self.assertTrue(evaluator.evaluate(self.cases, self.predictions)['passed'])

    def test_fabricated_citation_fails(self):
        self.predictions[0]['cited_chunk_ids'] = ['invented']
        self.assertFalse(evaluator.evaluate(self.cases, self.predictions)['passed'])

    def test_abstention_failure(self):
        self.predictions[1]['status'] = 'answered'
        self.assertFalse(evaluator.evaluate(self.cases, self.predictions)['passed'])

    def test_seed_cannot_be_quality_evidence(self):
        self.cases[0]['ready'] = False
        with self.assertRaises(ValueError):
            evaluator.evaluate(self.cases, self.predictions)

    def test_missing_and_duplicate_predictions_rejected(self):
        for predictions in [self.predictions[:1], self.predictions + [copy.deepcopy(self.predictions[0])]]:
            with self.assertRaises(ValueError):
                evaluator.evaluate(self.cases, predictions)

    def test_top_five_boundary(self):
        self.predictions[0]['retrieved_document_ids'] = ['x'] * 5 + ['doc']
        self.assertFalse(evaluator.evaluate(self.cases, self.predictions)['passed'])

    def test_no_answer_is_not_success_for_answerable_case(self):
        self.predictions[0]['status'] = 'insufficient_evidence'
        self.predictions[0]['cited_chunk_ids'] = []
        self.assertFalse(evaluator.evaluate(self.cases, self.predictions)['passed'])


class ConfigurationTests(unittest.TestCase):
    def test_repository_bootstrap_structure(self):
        self.assertGreater(checker.check(ROOT), 10)

    def test_pending_full_checks_exist_until_application_implemented(self):
        checks = runner.read_json(H / 'checks.json')['profiles']['full']
        self.assertTrue(any('pending' in item for item in checks))


if __name__ == '__main__':
    unittest.main()
