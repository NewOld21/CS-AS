#!/usr/bin/env python3
"""Evaluate recorded retrieval/citation results; does not call a model."""
import argparse
import json
import math
from pathlib import Path


def load_rows(path):
    rows = [json.loads(line) for line in Path(path).read_text(encoding='utf-8').splitlines() if line.strip()]
    ids = [row['id'] for row in rows]
    if len(set(ids)) != len(ids):
        raise ValueError('Duplicate case/prediction id')
    return rows


def evaluate(cases, predictions):
    if not cases or not all(c.get('ready') is True for c in cases):
        raise ValueError('Evaluation cases must be reviewed and ready=true')
    if len({c['id'] for c in cases}) != len(cases):
        raise ValueError('Duplicate cases')
    by_id = {p['id']: p for p in predictions}
    if len(by_id) != len(predictions) or set(by_id) != {c['id'] for c in cases}:
        raise ValueError('Prediction IDs must match cases exactly')
    hits = 0
    answerable = 0
    failures = []
    for case in cases:
        prediction = by_id[case['id']]
        if not isinstance(case.get('answerable'), bool):
            raise ValueError('answerable must be boolean')
        for name in ('retrieved_document_ids', 'retrieved_chunk_ids', 'cited_chunk_ids'):
            if not isinstance(prediction.get(name), list) or not all(isinstance(x, str) for x in prediction[name]):
                raise ValueError(f'{name} must be a list of strings')
        cited = prediction['cited_chunk_ids']
        if not set(cited).issubset(prediction['retrieved_chunk_ids']):
            failures.append({'id': case['id'], 'reason': 'citation_not_retrieved'})
        if case['answerable']:
            answerable += 1
            relevant = case.get('relevant_document_ids')
            if not isinstance(relevant, list) or not relevant or not all(isinstance(x, str) for x in relevant):
                raise ValueError('Answerable case needs actual relevant_document_ids')
            if set(relevant).intersection(prediction['retrieved_document_ids'][:5]):
                hits += 1
            if prediction.get('status') != 'answered' or not cited:
                failures.append({'id': case['id'], 'reason': 'missing_answer_or_citation'})
        elif prediction.get('status') != 'insufficient_evidence' or cited:
            failures.append({'id': case['id'], 'reason': 'must_abstain'})
    if not answerable or answerable == len(cases):
        raise ValueError('Require both answerable and unanswerable cases')
    return {'passed': hits >= math.ceil(answerable * 0.8) and not failures,
            'retrieval_hits_at_5': hits, 'answerable_cases': answerable,
            'retrieval_success_rate_at_5': hits / answerable, 'failures': failures,
            'limitations': ['Does not verify claim grounding or prompt-injection resistance']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cases', type=Path, required=True)
    parser.add_argument('--predictions', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        report = evaluate(load_rows(args.cases), load_rows(args.predictions))
    except (ValueError, KeyError, OSError) as error:
        report = {'passed': False, 'error': str(error)}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('PASS' if report['passed'] else 'FAIL')
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
