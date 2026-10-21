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
- 세션/CSRF·해시·만료 정책의 구현과 모델/임베딩 공급자·호출 제한 ([C02 결정](architecture.md))
- PostgreSQL·ChromaDB 앱 어댑터·마이그레이션·전용 테스트 DB
- 앱 이미지와 Compose 합류. DB용 Compose는 아래 C03 구성이다.

실행되지 않는 가짜 빌드 파일은 만들지 않는다. 버전 결정과 생성은 [다음 서비스 계획](exec-plans/active/002-service-bootstrap.md)에서 수행한다.
공통 명령 설명은 [scripts/README.md](../scripts/README.md), 상태·신뢰 경계는 [하네스 안내](../harness/README.md)를 따른다.

기존 `harness/tasks/001-bootstrap.json`은 이전 RAG 단독 범위다. 신규 학습 기능 실행 전 [하네스 연계](harness-workflow.md)의 task·검사 등록 전환이 필요하다. 현재 명령을 신규 제품 전체 검증으로 보고하지 않는다.

Windows에서 문서·구조 확인만 수행할 때는 `python -X utf8 scripts/check_docs.py`, `python -X utf8 harness/check.py`를 사용할 수 있다. 하네스 회귀·상태 실행기는 POSIX 환경이 필요하다. 서비스 실행 명령·포트·환경변수 템플릿은 실제 bootstrap 후 기록한다.

## 로컬 PostgreSQL·ChromaDB (C03)

Docker Engine + Compose v2 이상이 필요하다. 루트 [.env.example](../.env.example)을 `.env`로 복사하고 개발 전용 POSTGRES_PASSWORD를 채운다. 기존 `backend/.env.example`과 backend 환경은 AI 공급자 설정으로 보존한다. 루트 `.env`를 backend 파일로 덮어쓰거나 실제 비밀값을 커밋하지 않는다. Compose는 루트 `.env`를 자동 로드한다.

```sh
docker compose config --quiet
docker compose up -d --wait --wait-timeout 120
docker compose ps
docker compose exec postgres sh -c 'pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
curl --fail http://localhost:8000/api/v2/heartbeat
```

PostgreSQL `postgres:17.9-bookworm`과 Chroma `chromadb/chroma:1.5.3` 공식 이미지를 고정했다. PostgreSQL은 UTF8·UTC 기본값, `/var/lib/postgresql/data` named volume, Chroma는 `/data` named volume과 CHROMA_PERSIST_PATH를 사용한다. DB 이름/사용자/암호는 초기 빈 PostgreSQL 볼륨에서만 적용된다. 이후 `.env` 수정은 기존 계정을 변경하지 않는다. 도메인 테이블·migration은 후속 bootstrap이며 임의 초기 스키마를 생성하지 않는다.

| 실행 위치 | PostgreSQL | ChromaDB |
|---|---|---|
| 개발 호스트 | localhost:POSTGRES_PORT (기본 5432) | CHROMA_HOST=localhost, CHROMA_PORT=8000 |
| Compose data 네트워크 | postgres:5432 | chroma:8000 |

포트 충돌은 루트 `.env`의 공개 포트로 조정한다. 컨테이너 내부 포트는 바뀌지 않는다. 후속 Python 컨테이너는 같은 data 네트워크에 연결하고 CHROMA_HOST=chroma/CHROMA_PORT=8000을 명시하며 `depends_on: chroma: condition: service_healthy` 형태로 준비 상태를 기다린다. 현재 Compose에는 DB 두 개만 있다. host loopback 공개는 로컬 개발용이며 운영 공개/인증 구성이 아니다.

### 실제 읽기·쓰기와 영속성 검사

Python 3.11+ 가상환경에 [검증 클라이언트 잠금 파일](../scripts/requirements-local-db.lock.txt)을 설치한다. Windows는 아래 `python`을 `.venv\Scripts\python`으로 바꾼다.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r scripts/requirements-local-db.lock.txt
.venv/bin/python scripts/check_local_db.py write --state reports/local-db-smoke.json
docker compose restart
docker compose up -d --wait --wait-timeout 120
.venv/bin/python scripts/check_local_db.py read --state reports/local-db-smoke.json
docker compose down
docker compose up -d --wait --wait-timeout 120
.venv/bin/python scripts/check_local_db.py read --state reports/local-db-smoke.json
.venv/bin/python scripts/check_local_db.py cleanup --state reports/local-db-smoke.json
```

write는 UUID별 전용 SQL 테이블과 Chroma 컬렉션을 만들며 고정 3차원 벡터를 저장/검색한다. SQL UTF8 한글과 Chroma heartbeat/get/query를 검증하고 read는 같은 데이터를 재확인한다. 모델/API 키·임베딩 다운로드를 사용하지 않는다. cleanup은 해당 state의 검증 객체만 삭제한다. 다시 write하려면 새 state 경로를 사용한다. 테스트 테이블은 앱 데이터와 분리되며 실제 사용자 데이터나 기존 컬렉션을 변경하지 않는다.

`docker compose down`은 컨테이너/네트워크만 제거하고 named volume을 보존한다. restart/down/up 검사는 로컬 DB에만 수행한다. 전체 초기화는 **명시적으로 모든 로컬 데이터를 폐기할 때만** `docker compose down --volumes`를 사용한다. 일반 실행과 검증은 이 옵션을 사용하지 않는다. 볼륨을 제거하기 전에 백업한다.

공식 근거: [PostgreSQL 이미지의 초기화/볼륨](https://hub.docker.com/_/postgres), [Chroma 1.5.3 health check와 /data](https://cookbook.chromadb.dev/running/health-checks/), [Chroma 설정](https://cookbook.chromadb.dev/core/configuration/). 실제 검증 결과·이미지 digest·환경 제약은 [C03 계획](exec-plans/completed/010-c03-local-db.md)에 기록한다.

공식 health 예시의 curl은 실제 1.5.3 Rust 이미지에 포함되지 않는다. Compose는 이미지에 있는 Bash와 [읽기 전용 HTTP probe](../scripts/chroma-healthcheck.sh)로 같은 heartbeat의 HTTP 200을 검사한다. Python smoke는 SDK import 시 빈 임시 디렉터리를 사용하고 `_env_file=None`을 전달해 SDK가 루트 Compose `.env`를 자체 설정으로 해석하지 않게 한다. 앱 Python bootstrap도 이 설정 경계를 유지해야 한다.
