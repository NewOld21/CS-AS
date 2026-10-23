#!/usr/bin/env python3
"""Reproducible isolated Chroma checks; optional bounded real-model paired experiment."""
import argparse
import json
import os
import sys
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend/ai/src'))
from csas_rag.indexing.pipeline import ChunkConfig, chunk_document, incremental_index
from csas_rag.providers.chroma import ChromaVectorStore
from csas_rag.providers.embeddings import DeterministicTestEmbedding, OpenAIEmbedding
from csas_rag.providers.llm import OpenAIAnswerGenerator
from csas_rag.retrieval.vector import VectorRetriever
from csas_rag.retrieval.planning import QueryPlanner
from csas_rag.generation.answering import AnswerService

QUESTIONS = [
    'PostgreSQL에서 Read Committed의 각 SELECT는 같은 트랜잭션 안에서 항상 같은 스냅샷을 보는가?',
    'PostgreSQL Repeatable Read에서 동시 업데이트 충돌이 나면 애플리케이션은 어떻게 해야 하는가?',
    'HTTP GET 요청 본문은 모든 서버와 프록시가 같은 의미로 지원하는가?',
    'HTTP 304 응답 본문에 새 표현 전체를 담아 보내는가?',
    '문서에 근거가 없다면 2035년 PostgreSQL의 격리 수준 변경을 확정할 수 있는가?',
]


def run_isolated():
    class Counting(DeterministicTestEmbedding):
        calls = 0
        def embed(self, texts):
            self.calls += len(texts)
            return super().embed(texts)
    version = 'checklist-' + uuid.uuid4().hex
    store = ChromaVectorStore(version)
    embedding = Counting(64)
    documents = [{'source_id': 'checklist-fixture', 'document_id': f'doc:{i}', 'revision': 'r1',
                  'title': f'Fixture transaction {i}', 'content': '# Transaction\n' + ('transaction isolation memory index ' * (55+i)),
                  'source_url': 'https://example.org/fixture', 'locator': f'fixture:{i}',
                  'category': 'database' if i < 4 else 'network', 'language': 'en', 'concept_ids': []}
                 for i in range(8)]
    try:
        manifest, first = incremental_index(documents, store, embedding, version, 'fixture')
        before = store.count(); embedded = embedding.calls
        manifest, second = incremental_index(documents, store, embedding, version, 'fixture', manifest)
        reindex_calls = embedding.calls - embedded
        after = store.count()
        retriever = VectorRetriever(store, embedding, manifest)
        results = {}
        for k in (3, 5):
            results[str(k)] = [r['chunk_id'] for r in retriever.search('transaction isolation', k)]
        mmr = [r['chunk_id'] for r in retriever.search('transaction isolation', 5, search_type='mmr')]
        filtered = retriever.search('transaction isolation', 5, filters={'category': 'database'})
        timings = []
        calls = embedding.calls
        for _ in range(2):
            start = time.perf_counter(); retriever.search('unique repeat question', 5); timings.append(round((time.perf_counter()-start)*1000, 2))
        configs = [ChunkConfig(400, 50, 50, 'small'), ChunkConfig(1200, 180, 160, 'large')]
        chunk_counts = [sum(len(chunk_document(d, c)) for d in documents) for c in configs]
        result = {'provider': 'deterministic-test', 'storage': 'real isolated Chroma', 'documents': len(documents),
                  'generated_chunks': manifest['chunk_count'], 'first_count': before, 'second_count': after,
                  'reindex_embedding_calls': reindex_calls,
                  'idempotent': before == after, 'second_index_report': second,
                  'chunk_config_counts': chunk_counts, 'top_k': results, 'mmr': mmr,
                  'filtered_categories': [r['metadata']['category'] for r in filtered],
                  'repeat_query_ms': timings, 'repeat_query_embedding_calls': embedding.calls-calls,
                  'query_collection_count_unchanged': store.count() == after,
                  'representative_chunk': store.collection.get(limit=1, include=['documents','metadatas'])}
        result['passed'] = (before == after == manifest['chunk_count'] and chunk_counts[0] != chunk_counts[1]
                            and len(results['3']) == 3 and len(results['5']) == 5
                            and all(c == 'database' for c in result['filtered_categories'])
                            and result['repeat_query_embedding_calls'] == 1)
        return result
    finally:
        store.delete_index()


def compare(manifest_path):
    manifest = json.loads(Path(manifest_path).read_text(encoding='utf-8'))
    generator = OpenAIAnswerGenerator()
    embedding = OpenAIEmbedding(manifest['model'], manifest['dimensions'])
    retriever = VectorRetriever(ChromaVectorStore(manifest['index_version']), embedding, manifest)
    service = AnswerService(retriever, generator, planner=QueryPlanner())
    def pair(question):
        request = {'request_id': uuid.uuid4().hex, 'question': question, 'history': [], 'quiz_context': None,
                   'deadline_at': (datetime.now(timezone.utc)+timedelta(seconds=115)).isoformat(), 'index_version': manifest['index_version']}
        start = time.perf_counter()
        try:
            rag = service.answer(request)
            plain = generator.generate_bounded('Answer the CS question in Korean using your own knowledge. Return JSON {"answer":"..."}. Admit uncertainty. Do not claim access to documents.', question, 45)
            return {'question': question, 'rag': rag, 'no_rag': plain,
                    'elapsed_ms': round((time.perf_counter()-start)*1000,2), 'human_accuracy_review': 'UNVERIFIED'}
        except Exception as error:
            return {'question': question, 'status': 'FAILED', 'error_type': type(error).__name__}
    with ThreadPoolExecutor(max_workers=2) as pool:
        rows = list(pool.map(pair, QUESTIONS))
    return {'model': generator.model, 'embedding_model': embedding.model, 'index_version': manifest['index_version'],
            'same_model_and_generation_settings': True, 'results': rows, 'human_accuracy_review': 'UNVERIFIED'}


def live_probe(manifest_path):
    manifest = json.loads(Path(manifest_path).read_text(encoding='utf-8'))
    class Counting(OpenAIEmbedding):
        calls = 0
        def embed(self, texts):
            self.calls += len(texts)
            return super().embed(texts)
    embedding = Counting(manifest['model'], manifest['dimensions'])
    store = ChromaVectorStore(manifest['index_version'])
    service = AnswerService(VectorRetriever(store, embedding, manifest), OpenAIAnswerGenerator(), planner=QueryPlanner())
    before = store.count()
    rows = []
    for _ in range(2):
        request = {'request_id': uuid.uuid4().hex, 'question': QUESTIONS[0], 'history': [], 'quiz_context': None,
                   'deadline_at': (datetime.now(timezone.utc)+timedelta(seconds=115)).isoformat(),
                   'index_version': manifest['index_version'],
                   'retrieval': {'top_k': 3, 'filters': {'source_id': 'postgresql'}}}
        rows.append(service.answer(request))
    return {'results': rows, 'graph': service.graph.get_graph().draw_mermaid(),
            'collection_before': before, 'collection_after': store.count(), 'query_embedding_calls': embedding.calls,
            'filter_verified': all(c['source_id'] == 'postgresql' for row in rows for c in row['retrieved_chunks']),
            'repeat_total_ms': [r['diagnostics']['elapsed_ms'] for r in rows]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT/'reports/checklist/runtime.json')
    parser.add_argument('--compare-manifest', type=Path)
    parser.add_argument('--probe-manifest', type=Path)
    args = parser.parse_args()
    result = {'executed_at': datetime.now(timezone.utc).isoformat(), 'isolated': run_isolated()}
    if args.compare_manifest:
        result['model_comparison'] = compare(args.compare_manifest)
    if args.probe_manifest:
        result['live_probe'] = live_probe(args.probe_manifest)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'output': str(args.output), 'isolated_passed': result['isolated']['passed'], 'comparison_questions': len(result.get('model_comparison',{}).get('results',[]))}))
    return 0 if result['isolated']['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
