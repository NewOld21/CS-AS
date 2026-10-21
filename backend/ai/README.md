# AI / RAG

[작업 안내](AGENTS.md)를 읽는다. Python 서비스는 src/csas_rag/와 tests/에서 구현한다.
`src/csas_rag/ingestion/`의 오프라인 수집 CLI가 구현되어 있다. Python 3.11+ 표준 라이브러리만 사용하며 추가 런타임 패키지는 없다. 루트에서 `python3 scripts/ingest.py list`로 실행한다. 수집·샘플·검사는 [실행 안내](../../docs/runbooks/ingestion.md)를 따른다.

HTTP 엔드포인트·LangChain·PostgreSQL/pgvector는 후속 bootstrap이다. 서비스 의존성 잠금·Ruff/mypy 등록은 해당 작업에서 수행한다. 현재 unittest 검사는 수집 기능만 검증한다.
