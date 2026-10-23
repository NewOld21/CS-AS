# 27-item results

| No | Requirement | Target | Result | Evidence | Notes |
|---|---|---|---|---|---|
| 1 | F2001 | Index units/counts | PASS | [evidence/live-comparison.json](evidence/live-comparison.json) | 12 approved source documents; 673 live chunks. Isolated generated/store counts match. |
| 2 | F2002 | Idempotent indexing | PASS | [evidence/isolated.json](evidence/isolated.json) | Isolated counts 16 -> 16; unchanged incremental embedding calls 0. |
| 3 | F2003/F2004 | Two planning prompts | PASS | [evidence/live-comparison.json](evidence/live-comparison.json) | Real GMS keywords/candidates/selected/excluded IDs captured. Selection applies to existing indexed documents, not query-time ingestion. |
| 4 | F2004/NF2002 | Repeat without ingestion | PASS | [evidence/live-probe.json](evidence/live-probe.json) | Live collection 673 -> 673; query graph imports no collector. LLM rewriting caused 2 embedding calls across two requests; cache only shares identical rewritten queries. |
| 5 | F2005 | Chunk settings | PASS | [evidence/isolated.json](evidence/isolated.json) | Isolated configuration chunk totals: [49, 16] |
| 6 | F2006 | Top-K | PASS | [evidence/isolated.json](evidence/isolated.json) | Same isolated query returns 3 vs 5 actual Chroma rows. |
| 7 | F2007 | LangGraph | PASS | [evidence/live-probe.json](evidence/live-probe.json) | Real compiled retrieve/generate graph; executed traces and Mermaid recorded. |
| 8 | F2008 | Citations | PASS | [evidence/live-gms-evidence.png](evidence/live-gms-evidence.png) | Live browser evidence dialog and source numbering; forged ID/number/order regression tests. |
| 9 | F2007/F2008 | Abstention | PASS | [evidence/live-comparison.json](evidence/live-comparison.json) | Future PostgreSQL question returns insufficient_evidence with zero cited IDs; browser empty-source notice verified. |
| 10 | F2009 | Conversation isolation | PASS | [evidence/live-gms-multiturn.png](evidence/live-gms-multiturn.png) | Real browser new chat clears transcript; Spring owner-scoped history test and foreign-user 404. |
| 11 | F2011 | Metadata filters | PASS | [evidence/live-probe.json](evidence/live-probe.json) | Live source_id=postgresql restriction rechecked against all returned chunks. |
| 12 | F2010 | Domain evidence | FAIL | [evidence/generation-validation.json](evidence/generation-validation.json) | Live quiz AS has evidence. Actual generated quiz failed independent evidence audit (EXPLANATION_OR_DISTRACTOR_UNSUPPORTED), so live generation/submission/history happy path did not complete. Existing mock regressions passed. |
| 13 | F2012 | Progress/configuration errors | UNVERIFIED | [evidence/fixture-standalone-mobile.png](evidence/fixture-standalone-mobile.png) | Request progress and mocked missing-key UI verified. Actual missing-key/index deletion runtime probes still need an isolated configuration run. Never delete active index. |
| 14 | F2012 | High-risk disclaimer | NOT_APPLICABLE | Code/review | CS learning; no clinical or financial decision domain. |
| 15 | F2013 | Web UI | PASS | [evidence/live-gms-multiturn.png](evidence/live-gms-multiturn.png) | Actual Vue -> dedicated Spring/PostgreSQL -> Python LangGraph -> GMS/Chroma browser execution. |
| 16 | F2014 | Similarity/MMR | PASS | [evidence/isolated.json](evidence/isolated.json) | Both rankings executed against an isolated real Chroma collection. Test vectors verify diversity behavior; no quality superiority claim. |
| 17 | F2015 | Five-question comparison | UNVERIFIED | [evidence/live-comparison.json](evidence/live-comparison.json) | Five real same-model pairs executed and agent-reviewed; independent human accuracy/citation assessment remains pending. |
| 18 | F2015 | Comparison document | PASS | [evidence/live-comparison.json](evidence/live-comparison.json) | Actual paired outputs and limitations are included in rag-vs-no-rag.md. |
| 19 | F2016 | Source kinds | PASS | [evidence/fixture-standalone-desktop.png](evidence/fixture-standalone-desktop.png) | UI distinguishes GitHub/Wikipedia/external technical documents/development fixtures; quiz context labeled separately. |
| 20 | NF2001 | Latency | UNVERIFIED | [evidence/live-probe.json](evidence/live-probe.json) | Live first/repeat RAG ms: [21616.71, 15801.04]; user acceptability not judged automatically. |
| 21 | NF2003/NF2004 | Secrets/errors | UNVERIFIED | Code/review | Ignored environment and sanitized errors implemented; exact current-key scan is recorded separately in test-results.md. Independent visual audit pending. |
| 22 | NF2005 | Modules | PASS | Code/review | ingestion/indexing/retrieval/generation/providers and Vue/Spring separated; no broad rewrite. |
| 23 | NF2006 | HTTP policy | PASS | [evidence/corpus-probes.json](evidence/corpus-probes.json) | Existing retry/backoff/Retry-After/timeout tests, approved source gates and configured contact; bounded sample collection completed. |
| 24 | NF2007 | Source terms | PASS | [evidence/source-policies.json](evidence/source-policies.json) | Approved registry license/attribution/URL/storage policies summarized in README and source-policies.json. |
| 25 | Required | Combined result | UNVERIFIED | Code/review | Unverified individual checks and independent peer review remain; not an all-pass submission. |
| 26 | Required | Screenshots | UNVERIFIED | Code/review | Real browser screenshots included. Dedicated captures for every numerical/configuration-error checklist item remain to be completed. Raw execution JSON is supplied. |
| 27 | Required | Submission files | PASS | Code/review | Requirements, architecture, results, matrix, comparison, checklist and evidence are packaged; source remains in this Git repository. |
