# Test execution evidence

2026-10-23 KST, branch feat/standalone-rag-checklist. No production/development DB test accounts were created; live browser tests use isolated PostgreSQL on backend port 18080.

| Layer | Command | Observed result |
|---|---|---|
| Python / real Chroma | `docker compose exec -T -e CSAS_CHROMA_INTEGRATION=1 ai python -m unittest discover -s backend/ai/tests -v` | 85 passed, no skips |
| Java / isolated PostgreSQL | Gradle `--init-script config/isolated-build.gradle --no-daemon spotlessApply check bootJar` with independent GRADLE_USER_HOME | 56 passed; format, Checkstyle and JAR passed |
| Vue | `npm run build`, `npm test`, `npm run lint`, `npm run format:check` | build/typecheck passed; 17 unit tests; lint/format passed |
| Browser fixtures | Chrome `ui.spec.ts history.spec.ts chat.spec.ts` | 13 passed; includes 390px/WCAG and source dialog |
| Browser GMS | Chrome `chat-live.spec.ts`, `CSAS_CHAT_E2E_API=http://localhost:18080` | standalone multi-turn/refresh/new session and document-covered quiz AS passed in 49.1s; subsequent generation/history extension recorded separately |
| Common harness | Linux snapshot `python3 scripts/verify.py` | 19 harness tests and configuration passed; first docs check caught missing test-results.md during packaging, corrected before final check |

Java initial concurrent bootRun/test builds collided on output/JPA discovery, then shared Gradle journal locking. Final run used `gradle -g /tmp/csas-check-gradle --init-script config/isolated-build.gradle`; dependency artifacts were copied into that independent cache. No tests were weakened or skipped. Fixture browser first saw an old Docker Vite route cache (404); frontend restart loaded /chat. An initial live index-maintenance quiz AS correctly abstained because the bounded corpus lacks index-maintenance documentation; the covered Read Committed quiz verified the same contextual AS path.

Live paired experiment: GMS gpt-5-mini / text-embedding-3-large, 3072 dimensions, 12 approved documents, 673 chunks, index csas-checklist-live-v1. Five source-presence probes passed; this is not a 20-query relevance score. Four paired RAG questions answered with citations; one future-version question abstained. First/repeat RAG processing: 21616.71 / 15801.04 ms. Rewritten queries differed and caused two query embeddings; exact-query vector cache is not claimed to eliminate every repeat embedding.

Runtime errors: missing-key and missing-index code paths exist; UI missing-key/empty-evidence fixture checks passed. Actual isolated missing-key/index runtime probes and complete per-item screenshots remain unverified. Independent human fact review, usability judgment and peer signatures are not complete.

Security: environment files are ignored and never packaged. A current-key exact-match scan is performed before commit; scan result is recorded in the execution plan. Historical early trace field collection_events=0 was a constant and is not used as observed ingestion evidence. Request graph separation, real collection counts and recorded operations are the evidence instead.

Final live extension: the covered Read Committed quiz was deliberately answered incorrectly, AS returned sources, and related quiz generation reached the independent evidence audit. The candidate was rejected with EXPLANATION_OR_DISTRACTOR_UNSUPPORTED. The happy-path browser assertion requiring a READY generated quiz therefore failed; no failed candidate was published. Actual GMS generated-quiz submission/history in this run remains unverified. Existing deterministic/mock generated-quiz regressions passed. This opt-in live test preserves the requirement rather than treating a rejection as success.

Exact current GMS key scan across tracked and candidate non-environment source/submission files: 0 matches. Actual live multi-turn screenshot was visually inspected: no key, full prompt or stack trace displayed.

Final Linux candidate common verification passed: 354 local links, bootstrap configuration, 19 harness tests. This is the bootstrap profile, not a claim that all product or 27-item acceptance checks passed.
