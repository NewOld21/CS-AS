# RAG adapter

[공통 개발 가이드](../../docs/08_AGENTS.md), [아키텍처](../../docs/05_ARCHITECTURE.md),
[수집](../../docs/domain/ingestion.md), [검색](../../docs/domain/retrieval.md),
[답변](../../docs/domain/answering.md), [테스트](../../docs/09_TEST_SCENARIO.md)를 읽는다.

Python/LangChain은 src/csas_rag/와 tests/에서 구현한다. Java와 프로세스·의존성을 분리한다.
수집·검색·생성·공급자 어댑터를 분리하고 원문을 실행 지시로 취급하지 않는다.
공개 API는 Spring Boot가 제공한다. 내부 API 계약은 구현 전 docs/07_API_SPEC.md의 미결정 항목을 확정한다.
평가 원본은 루트 harness/evals/다. 테스트 통과를 위해 평가셋을 완화하지 않는다.
