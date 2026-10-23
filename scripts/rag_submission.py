#!/usr/bin/env python3
"""Package observed checklist evidence. Missing/human checks remain UNVERIFIED."""
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'docs/submission'


def main():
    evidence = OUT/'evidence'; evidence.mkdir(parents=True, exist_ok=True)
    for name in ('isolated.json', 'live-comparison.json', 'live-probe.json', 'corpus-probes.json'):
        source = ROOT/'reports/checklist'/name
        if source.exists(): shutil.copy2(source, evidence/name)
    for source in (ROOT/'reports/checklist/evidence').glob('*.png'):
        name = 'fixture-'+source.name if source.name.startswith('standalone-') else source.name
        shutil.copy2(source, evidence/name)
    comparison = json.loads((evidence/'live-comparison.json').read_text(encoding='utf-8'))
    probe = json.loads((evidence/'live-probe.json').read_text(encoding='utf-8'))['live_probe']
    isolated = comparison['isolated']
    definitions = [
      ('F2001','Index units/counts','PASS','12 approved source documents; 673 live chunks. Isolated generated/store counts match.','live-comparison.json'),
      ('F2002','Idempotent indexing','PASS',f"Isolated counts {isolated['first_count']} -> {isolated['second_count']}; unchanged incremental embedding calls 0.",'isolated.json'),
      ('F2003/F2004','Two planning prompts','PASS','Real GMS keywords/candidates/selected/excluded IDs captured. Selection applies to existing indexed documents, not query-time ingestion.','live-comparison.json'),
      ('F2004/NF2002','Repeat without ingestion','PASS',f"Live collection {probe['collection_before']} -> {probe['collection_after']}; query graph imports no collector. LLM rewriting caused {probe['query_embedding_calls']} embedding calls across two requests; cache only shares identical rewritten queries.",'live-probe.json'),
      ('F2005','Chunk settings','PASS',f"Isolated configuration chunk totals: {isolated['chunk_config_counts']}",'isolated.json'),
      ('F2006','Top-K','PASS','Same isolated query returns 3 vs 5 actual Chroma rows.','isolated.json'),
      ('F2007','LangGraph','PASS','Real compiled retrieve/generate graph; executed traces and Mermaid recorded.','live-probe.json'),
      ('F2008','Citations','PASS','Live browser evidence dialog and source numbering; forged ID/number/order regression tests.','live-gms-evidence.png'),
      ('F2007/F2008','Abstention','PASS','Future PostgreSQL question returns insufficient_evidence with zero cited IDs; browser empty-source notice verified.','live-comparison.json'),
      ('F2009','Conversation isolation','PASS','Real browser new chat clears transcript; Spring owner-scoped history test and foreign-user 404.','live-gms-multiturn.png'),
      ('F2011','Metadata filters','PASS','Live source_id=postgresql restriction rechecked against all returned chunks.','live-probe.json'),
      ('F2010','Domain evidence','PASS','Live quiz AS evidence; generated quiz grading/history regression uses GMS mock unless live-generated-history.png is present.','live-quiz-as.png'),
      ('F2012','Progress/configuration errors','UNVERIFIED','Request progress and mocked missing-key UI verified. Actual missing-key/index deletion runtime probes still need an isolated configuration run. Never delete active index.','fixture-standalone-mobile.png'),
      ('F2012','High-risk disclaimer','NOT_APPLICABLE','CS learning; no clinical or financial decision domain.',''),
      ('F2013','Web UI','PASS','Actual Vue -> dedicated Spring/PostgreSQL -> Python LangGraph -> GMS/Chroma browser execution.','live-gms-multiturn.png'),
      ('F2014','Similarity/MMR','PASS','Both rankings executed against an isolated real Chroma collection. Test vectors verify diversity behavior; no quality superiority claim.','isolated.json'),
      ('F2015','Five-question comparison','UNVERIFIED','Five real same-model pairs executed and agent-reviewed; independent human accuracy/citation assessment remains pending.','live-comparison.json'),
      ('F2015','Comparison document','PASS','Actual paired outputs and limitations are included in rag-vs-no-rag.md.','live-comparison.json'),
      ('F2016','Source kinds','PASS','UI distinguishes GitHub/Wikipedia/external technical documents/development fixtures; quiz context labeled separately.','fixture-standalone-desktop.png'),
      ('NF2001','Latency','UNVERIFIED',f"Live first/repeat RAG ms: {probe['repeat_total_ms']}; user acceptability not judged automatically.",'live-probe.json'),
      ('NF2003/NF2004','Secrets/errors','UNVERIFIED','Ignored environment and sanitized errors implemented; exact current-key scan is recorded separately in test-results.md. Independent visual audit pending.',''),
      ('NF2005','Modules','PASS','ingestion/indexing/retrieval/generation/providers and Vue/Spring separated; no broad rewrite.',''),
      ('NF2006','HTTP policy','PASS','Existing retry/backoff/Retry-After/timeout tests, approved source gates and configured contact; bounded sample collection completed.','corpus-probes.json'),
      ('NF2007','Source terms','PASS','Approved registry license/attribution/URL/storage policies summarized in README and source-policies.json.','source-policies.json'),
      ('Required','Combined result','UNVERIFIED','Unverified individual checks and independent peer review remain; not an all-pass submission.',''),
      ('Required','Screenshots','UNVERIFIED','Real browser screenshots included. Dedicated captures for every numerical/configuration-error checklist item remain to be completed. Raw execution JSON is supplied.',''),
      ('Required','Submission files','PASS','Requirements, architecture, results, matrix, comparison, checklist and evidence are packaged; source remains in this Git repository.',''),
    ]
    rows=[]
    for number, (requirement, target, status, note, filename) in enumerate(definitions,1):
        rows.append({'number':number,'requirement':requirement,'target':target,'result':status,'evidence':f'evidence/{filename}' if filename else '', 'note':note})
    registry=json.loads((ROOT/'docs/data-sources.json').read_text(encoding='utf-8'))
    used={'gyoogle','wikipedia-ko','mdn-http','postgresql','rfc-editor'}
    policies=[{k:s.get(k) for k in ('id','license','attribution','storage_policy','usage_review','enabled','review','allowed_urls')} for s in registry['sources'] if s['id'] in used]
    (evidence/'source-policies.json').write_text(json.dumps(policies,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (OUT/'requirements-matrix.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    table='| No | Requirement | Target | Result | Evidence | Notes |\n|---|---|---|---|---|---|\n'
    for row in rows:
        link=f"[{row['evidence']}]({row['evidence']})" if row['evidence'] else 'Code/review'
        table+=f"| {row['number']} | {row['requirement']} | {row['target']} | {row['result']} | {link} | {row['note']} |\n"
    (OUT/'requirements-matrix.md').write_text('# 27-item results\n\n'+table,encoding='utf-8')
    counts={status:sum(r['result']==status for r in rows) for status in ('PASS','FAIL','UNVERIFIED','NOT_APPLICABLE')}
    pdfs=list(ROOT.glob('*.pdf')); digest=hashlib.sha256(pdfs[0].read_bytes()).hexdigest() if pdfs else 'not provided'
    (OUT/'checklist-results.md').write_text('# Self / peer checklist\n\nSelf execution: 2026-10-23 KST. Original PDF: four pages, 27 rows, optional items 15–19. PDF SHA256: `'+digest+'`.\n\n'+str(counts)+'\n\nPeer reviewer, author signature and independent human assessment: NOT PERFORMED. Do not mark these as completed. See [matrix](requirements-matrix.md) for results/evidence/reasons.\n',encoding='utf-8')
    (OUT/'requirements.md').write_text('# Requirements\n\nStandalone authenticated /chat and existing quiz AS share one RAG engine. Session-local history rewrites retrieval. GMS search planning, real Chroma metadata filters, configurable Top-K/MMR and LangGraph retrieve/generate lead to bounded grounded generation and validated citations. Ingestion is approved offline batch work. No arbitrary URL fetching on user questions.\n\nOriginal checklist row 1 distinguishes document vs generated chunk units; row 3 is adapted to selection from existing approved indexed candidates. Rows 15–19 are selected advanced features. Row 14 does not apply. The supplied PDF and [matrix](requirements-matrix.md) are the assessment basis.\n',encoding='utf-8')
    (OUT/'rag-architecture.md').write_text('# RAG architecture\n\nVue /chat or quiz AS -> owner-authenticated Spring sessions/history -> Python AnswerService.graph.invoke -> retrieve (structured query extraction, exact metadata filter, Chroma similarity/MMR, structured candidate selection) -> generate (GMS bounded JSON, citation IDs/order/numbers) -> Spring PostgreSQL answer/citation snapshots -> safe Vue Markdown/code/evidence panel.\n\nThe graph stores no cross-session conversation state. A bounded hashed query-vector cache stores embeddings only. The offline deterministic provider is explicitly reported by /chat/status; GMS without key/index does not silently substitute canned answers.\n\nActual graph: [execution evidence](evidence/live-probe.json). API basis: [LangGraph StateGraph reference](https://reference.langchain.com/python/langgraph/graph/state/StateGraph).\n',encoding='utf-8')
    experiment='# RAG vs no RAG\n\nFive actual GMS gpt-5-mini pairs; same model/provider settings. RAG additionally gets approved indexed documents. Stored raw outputs: [JSON](evidence/live-comparison.json). No claim that retrieval always improves correctness. Independent human review remains UNVERIFIED.\n\n'
    for i,row in enumerate(comparison['model_comparison']['results'],1):
        experiment+=f"## {i}. {row['question']}\n\nRAG status: {row['rag']['status']}; graph latency {row['rag']['diagnostics']['elapsed_ms']} ms.\n\n{row['rag'].get('answer') or 'Insufficient evidence; no cited documents.'}\n\nNo-RAG:\n\n{row['no_rag'].get('answer','')}\n\n"
    experiment+='## Review limits\n\nAgent comparison: core conclusions in pairs 1, 3, 4 match the saved PostgreSQL/RFC evidence. Pair 2 correctly recommends full transaction retry, but language implying retry always eliminates all conflicts is too strong: another concurrent conflict can recur. Pair 5 abstains in both conditions. No-RAG answers in this sample did not invent source URLs, so this run does not establish a hallucination-rate advantage. Evidence presence is not full semantic correctness. Historical collection_events=0 diagnostic fields in early raw traces were constants, not measured counters; use collection counts and actual graph separation instead.\n'
    (OUT/'rag-vs-no-rag.md').write_text(experiment,encoding='utf-8')
    (OUT/'README.md').write_text('# Submission package\n\nRead [requirements](requirements.md), [architecture](rag-architecture.md), [test results](test-results.md), [27-item matrix](requirements-matrix.md), [RAG comparison](rag-vs-no-rag.md), [self/peer checklist](checklist-results.md). Source code is the parent Git repository. This is a self-executed package, not a signed peer review.\n\nEvidence JSON uses actual GMS/Chroma runs except explicitly labeled isolated deterministic fixtures. Screenshot names beginning fixture- use routed API fixtures; live- use actual GMS and a dedicated test DB. Active development DB contains no test accounts from these runs.\n\nReproduce: Docker AI `python scripts/rag_checklist.py --output reports/checklist/live-comparison.json --compare-manifest data/processed/indexes/csas-checklist-live-v1.json`; repeat/filter probe uses `--probe-manifest`. Package after execution with `python scripts/rag_submission.py`. Never replace missing evidence with invented responses.\n',encoding='utf-8')
    print(json.dumps(counts))


if __name__ == '__main__': main()
