# Development

## 현재 실행 가능한 명령
Linux/POSIX, Python 3.11 이상을 사용한다. 하네스 런타임은 Python 표준 라이브러리만 사용한다.
저장소 루트에서 실행한다.

```sh
python3 scripts/verify.py
python3 scripts/task.py init --state-dir /tmp/csas-run --task harness/tasks/001-bootstrap.json
python3 scripts/task.py verify --state-dir /tmp/csas-run --profile bootstrap
python3 scripts/task.py handoff --state-dir /tmp/csas-run
```

긴 작업은 /tmp 대신 저장소 밖 영속 볼륨을 사용한다. Windows에서는 Docker/WSL의 Linux 환경에서 실행한다.
전용 상태 경로는 실행 관리자가 소유하며 기존 실행을 지워 예산을 초기화하지 않는다.

## 서비스 생성 때 결정할 항목

Python 오프라인 수집은 `python3 scripts/ingest.py list`로 실행한다. 출처·샘플·증분·재시도·독립 검사는 [수집 안내](runbooks/ingestion.md)를 따른다. 표준 라이브러리만 사용하며 HTTP 서비스·LangChain bootstrap은 후속이다.
스택과 제품 범위는 [ADR 0003](13_PHASE0_DECISIONS.md)으로 확정했다. 아래는 버전·실행 설정 결정 항목이며, 22시간 제한은 적용하지 않는다.
- JDK·Spring Boot·Gradle Wrapper와 포맷·정적 분석 플러그인
- Node·Vue·TypeScript·패키지 매니저·lockfile
- Python·LangChain·의존성 잠금·Ruff·mypy·pytest
- 내부 HTTP API·timeout·오류 계약
- 세션·CSRF·비밀번호 해시·만료 시간·모델/임베딩 공급자·호출 제한
- PostgreSQL/pgvector·마이그레이션·전용 테스트 DB
- Docker 이미지와 Compose. 현재 서비스용 compose.yaml은 아직 없다.

실행되지 않는 가짜 빌드 파일은 만들지 않는다. 버전 결정과 생성은 [다음 서비스 계획](exec-plans/active/002-service-bootstrap.md)에서 수행한다.
공통 명령 설명은 [scripts/README.md](../scripts/README.md), 상태·신뢰 경계는 [하네스 안내](../harness/README.md)를 따른다.

기존 `harness/tasks/001-bootstrap.json`은 이전 RAG 단독 범위다. 신규 학습 기능 실행 전 [하네스 연계](harness-workflow.md)의 task·검사 등록 전환이 필요하다. 현재 명령을 신규 제품 전체 검증으로 보고하지 않는다.

Windows에서 문서·구조 확인만 수행할 때는 `python -X utf8 scripts/check_docs.py`, `python -X utf8 harness/check.py`를 사용할 수 있다. 하네스 회귀·상태 실행기는 POSIX 환경이 필요하다. 서비스 실행 명령·포트·환경변수 템플릿은 실제 bootstrap 후 기록한다.
