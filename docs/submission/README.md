# Submission package

Read [requirements](requirements.md), [architecture](rag-architecture.md), [test results](test-results.md), [27-item matrix](requirements-matrix.md), [RAG comparison](rag-vs-no-rag.md), [self/peer checklist](checklist-results.md). Source code is the parent Git repository. This is a self-executed package, not a signed peer review.

Evidence JSON uses actual GMS/Chroma runs except explicitly labeled isolated deterministic fixtures. Screenshot names beginning fixture- use routed API fixtures; live- use actual GMS and a dedicated test DB. Active development DB contains no test accounts from these runs.

Reproduce: Docker AI `python scripts/rag_checklist.py --output reports/checklist/live-comparison.json --compare-manifest data/processed/indexes/csas-checklist-live-v1.json`; repeat/filter probe uses `--probe-manifest`. Package after execution with `python scripts/rag_submission.py`. Never replace missing evidence with invented responses.
