import copy
import unittest

from test_answering import AnswerService, GenerationError, Generator, Retriever, ROW, answer_request
from csas_rag.retrieval.planning import QueryPlanner
from csas_rag.retrieval.vector import VectorRetriever


class PlannedGenerator(Generator):
    def generate(self, system, prompt):
        if system.startswith('Extract CS'):
            return {'query': 'database transaction isolation', 'keywords': ['transaction', 'isolation'], 'filters': {}}
        if system.startswith('Select relevant'):
            return {'selected_chunk_ids': ['chunk:one'], 'excluded': []}
        return super().generate(system, prompt)


class GraphRagTests(unittest.TestCase):
    def test_real_graph_nodes_and_two_prompt_plan(self):
        service = AnswerService(Retriever(), PlannedGenerator(), planner=QueryPlanner())
        result = service.answer(answer_request())
        self.assertIn('retrieve', service.graph.get_graph().nodes)
        self.assertIn('generate', service.graph.get_graph().nodes)
        self.assertEqual(result['diagnostics']['keywords'], ['transaction', 'isolation'])
        self.assertEqual(result['diagnostics']['selected_chunk_ids'], ['chunk:one'])
        self.assertIn('[1]', result['answer'])

    def test_followup_retrieval_uses_only_supplied_history(self):
        retriever = Retriever()
        service = AnswerService(retriever, Generator())
        request = {**answer_request(), 'question': 'Explain more simply',
                   'history': [{'role': 'user', 'content': 'transaction isolation'}]}
        service.answer(request)
        self.assertIn('transaction isolation', retriever.last_question)
        service.answer(answer_request())
        self.assertNotIn('transaction isolation', retriever.last_question)

    def test_forged_selection_fails_closed(self):
        class Forged(PlannedGenerator):
            def generate(self, system, prompt):
                if system.startswith('Select relevant'):
                    return {'selected_chunk_ids': ['not-retrieved']}
                return super().generate(system, prompt)
        with self.assertRaises(GenerationError):
            AnswerService(Retriever(), Forged(), planner=QueryPlanner()).answer(answer_request())

    def test_citation_order_is_model_id_order_and_numbers_are_checked(self):
        second = copy.deepcopy(ROW); second['chunk_id'] = 'chunk:two'
        generated = Generator({'status': 'answered', 'answer': 'Second [1], first [2]',
                               'cited_chunk_ids': ['chunk:two', 'chunk:one']})
        result = AnswerService(Retriever([ROW, second]), generated).answer(answer_request())
        self.assertEqual(result['retrieved_chunks'][0]['chunk_id'], 'chunk:two')
        generated.result['answer'] = 'Wrong [3]'
        with self.assertRaises(GenerationError):
            AnswerService(Retriever([ROW, second]), generated).answer(answer_request())

    def test_empty_selection_skips_answer_call(self):
        class Empty(PlannedGenerator):
            def generate(self, system, prompt):
                if system.startswith('Select relevant'):
                    return {'selected_chunk_ids': []}
                if system.startswith('You answer'):
                    raise AssertionError('must not generate')
                return super().generate(system, prompt)
        self.assertEqual(AnswerService(Retriever(), Empty(), planner=QueryPlanner()).answer(answer_request())['status'], 'insufficient_evidence')

    def test_filter_revalidation_mmr_and_query_embedding_cache(self):
        class Embedding:
            model = 'mock'; dimensions = 2; calls = 0
            def embed(self, texts):
                self.calls += 1
                return [[1., 0.]]
        class Store:
            def query(self, vector, limit, where=None):
                self.where = where
                return [{'chunk_id': str(n), 'score': 1, 'content': str(n), 'metadata': {'category': category}}
                        for n, category in [(1, 'database'), (2, 'network'), (3, 'database')]][:limit]
            def get_embeddings(self, ids):
                return {i: [1., 0.] if i == '1' else [0., 1.] for i in ids}
        embedding, store = Embedding(), Store()
        retriever = VectorRetriever(store, embedding, {'model': 'mock', 'dimensions': 2})
        rows = retriever.search('query', 3, filters={'category': 'database'}, search_type='mmr')
        self.assertEqual([r['chunk_id'] for r in rows], ['1', '3'])
        self.assertEqual(store.where, {'category': 'database'})
        retriever.search('query', 3)
        self.assertEqual(embedding.calls, 1)
        with self.assertRaises(ValueError):
            retriever.search('query', 3, filters={'$where': 'injection'})

    def test_invalid_topk_and_expired_deadline(self):
        for limit in (0, 21, True):
            with self.assertRaises(ValueError):
                AnswerService(Retriever(), Generator()).answer({**answer_request(), 'retrieval': {'top_k': limit}})
        with self.assertRaises(TimeoutError):
            AnswerService(Retriever(), Generator()).answer({**answer_request(), 'deadline_at': '2020-01-01T00:00:00Z'})
