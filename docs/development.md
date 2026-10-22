# Development

## Docker 전체 개발 스택

일상 개발 실행은 저장소 루트의 Compose를 기준으로 한다. 호스트에 Node.js·JDK·Python을 설치하지 않아도 frontend, Spring Boot backend, 로컬 RAG adapter, PostgreSQL, ChromaDB가 함께 실행된다.

```sh
docker compose up -d --build --wait --wait-timeout 240
docker compose ps
docker compose logs -f frontend backend ai
```

브라우저 주소는 http://localhost:5173 이다. Vite의 `/api` 프록시는 Compose 내부의 `backend:8080`을 사용하고, backend는 `ai:8090`, AI는 `chroma:8000`을 사용한다. 모든 호스트 포트는 loopback에만 바인딩한다. 일반 종료는 볼륨을 보존하는 `docker compose down`을 사용한다.

기본 AI는 `backend/.env`의 GMS 설정과 루트 `.env`의 `RAG_ACTIVE_INDEX`를 읽는다. 해당 ACTIVE manifest가 있으면 그 manifest에 기록된 임베딩 모델·차원을 그대로 사용하며 fixture를 적재하지 않는다. manifest가 없는 개발 인덱스에서만 `backend/ai/fixtures/local_documents.json`을 seed한다. 현재 Docker 기본값은 승인 실코퍼스 `csas-live-20261023-v4`다.

```sh
# 비밀값 없는 라이브 진단 결과는 reports/에 저장한다.
docker compose run --rm --no-deps ai python scripts/rag_diagnostics.py \
  --output reports/rag-live-diagnostics.json
docker compose run --rm --no-deps ai python scripts/rag_e2e.py \
  --output reports/rag-live-e2e.json
```

외부 호출 없는 개발은 루트 `.env`에 `RAG_DEV_PROVIDER=deterministic-test`, `RAG_ACTIVE_INDEX=local-dev-v1`을 지정한다. GMS 키, 요청 Authorization, 전체 환경변수는 출력하지 않는다.

## Vue 로컬 UI (012, C17)

Node 22.12+(검증 24.18.0)/npm, 설치는 frontend/에서 `npm ci`다. 버전은 package.json/package-lock.json으로 고정한다. 루트 공통 명령:

```sh
python scripts/frontend.py dev
python scripts/frontend.py check
python scripts/frontend.py e2e
```

개발 주소는 http://localhost:5173 이다. Vite가 같은 출처의 `/api/v1`을 기본 localhost:8080 Spring으로 프록시한다. 서버 API·세션·CSRF·인증 정책을 변경하지 않는다. `CSAS_API_TARGET`은 개발 서버 측 프록시 대상을 바꾸는 선택 설정이며 브라우저 번들에 비밀값을 넣지 않는다. 프론트 상태와 CSRF는 메모리만 사용하고 쿠키는 HttpOnly 서버 쿠키를 그대로 전송한다. 토큰/비밀번호를 localStorage에 저장하거나 출력하지 않는다. 변경 POST는 자동 재전송하지 않는다.

실제 인증 E2E는 **전용 테스트 DB**를 사용한다. 기존 compose.backend-test.yaml의 PostgreSQL/checks를 그대로 사용해 별도 앱 포트를 연다. 테스트 회원을 개발/운영 DB에 만들지 않는다.

```sh
docker compose -f compose.backend-test.yaml run --rm -d --name csas-ui-auth-check --publish 127.0.0.1:18080:8080 checks gradle --no-daemon bootRun
# 앱 readiness 후 POSIX: CSAS_E2E_API=http://localhost:18080 python scripts/frontend.py e2e
# PowerShell: $env:CSAS_E2E_API='http://localhost:18080'; python scripts/frontend.py e2e
docker stop csas-ui-auth-check
```

Playwright는 기본 설치된 Chrome을 사용한다. 다른 환경에서는 `PLAYWRIGHT_CHANNEL=chromium` 및 해당 Playwright 브라우저 설치를 사용한다. 실제 API E2E는 CSAS_E2E_API가 없으면 명시적으로 skip한다. C17의 fixture 브라우저 검사는 퀴즈→채점→문맥 세션→답변/출처 UI를 재현하며, Spring/PostgreSQL 문맥·저장은 별도 통합 검사로 검증한다. UI fixture를 외부 LLM/실제 코퍼스 성공으로 보고하지 않는다. 결과·스크린샷은 Git 제외 reports/ui-qa/에 저장한다.

## Java backend (C04~C17)

호스트 실행은 JDK 21과 backend/의 Gradle Wrapper 8.14.3을 사용한다. Spring Boot 3.5.16, Flyway와 PostgreSQL 드라이버는 BOM 및 gradle.lockfile로 고정한다. `DB_URL`, `DB_USER`, `DB_PASSWORD`를 지정하고 `cd backend && ./gradlew bootRun`으로 실행한다. Windows는 `gradlew.bat`을 사용한다. `.env` 파일을 Spring이 자동 로드하지 않으며 backend의 기존 AI 공급자 환경 파일도 읽지 않는다.

```sh
# 공통 실행 진입점 (아래 Compose 명령과 동일)
python scripts/backend.py up
python scripts/backend.py check
# 루트 .env의 로컬 DB와 연동, HTTP 개발 쿠키 프로필 명시
docker compose up -d backend
# DB 포함 readiness: 정상 200 {"status":"UP"}, DB 장애 503 {"status":"DOWN"}
curl --fail http://localhost:8080/health
# 별도 PostgreSQL tmpfs 테스트 DB; 개발 DB/volume과 분리
docker compose -f compose.backend-test.yaml up -d --wait postgres-test
docker compose -f compose.backend-test.yaml run --rm checks
```

정적 타입 검사는 Java 컴파일러, formatter는 Spotless/google-java-format, 정적 검사는 Checkstyle이다. `./gradlew spotlessApply`로 포맷하고 `./gradlew check bootJar`로 검사한다. backend/build/reports/tests/test/index.html과 checkstyle 보고서에 결과를 기록한다. Wrapper와 dependency lock은 버전을 변경할 때만 갱신한다.

Flyway는 csas schema의 flyway_schema_history에서 적용 이력을 관리하며 앱 기동 시 migration/검증 후 서버를 연다. Hibernate는 `validate`만 수행하며 ddl-auto create/update·Flyway clean·baseline-on-migrate는 사용하지 않는다. 적용된 SQL은 수정하지 않고 새 Vn migration을 추가한다. 실패 시 로그의 버전/SQLSTATE를 확인하고 데이터를 지우지 않은 채 원인을 수정한다. `/health`는 익명 공개이며 DB URL·암호·컴포넌트 상세를 반환하지 않는다. 프로세스가 살아 있어도 DB 연결 실패는 DOWN이다.

테스트 DB 암호는 compose.backend-test.yaml의 공개 테스트 전용 값이며 호스트 포트를 열지 않는다. 테스트 DB 데이터는 tmpfs이고 이 전용 Compose를 down하면 사라진다. 루트 개발 DB 볼륨에는 영향이 없다. 컨테이너에는 src/·빌드 설정·출력만 개별 마운트해 backend/.env 및 AI 공급자 키를 노출하지 않는다. 일반 서버 설정은 Secure=true이고 명시한 local 프로필에서만 HTTP 쿠키 예외와 localhost:5173 CORS를 허용한다. 임의 Origin/와일드카드 credentials를 허용하지 않는다.

가입·로그인 전 `GET /api/v1/auth/csrf`의 token과 CSAS_SESSION 쿠키를 함께 유지한다. POST에 `X-CSRF-Token`을 보내고 로그인 성공 후 토큰을 다시 받는다. 가입은 `/api/v1/auth/signup`(201), 로그인은 `/api/v1/auth/login`(200), 본인 조회는 `/api/v1/auth/me`(200), 로그아웃은 `/api/v1/auth/logout`(204)이다. 로그아웃 후 재접근/중복 로그아웃은 401이다. 가입/로그인 예시는 [API 계약](api/openapi.yaml)을 따른다. 비밀번호/쿠키/token을 출력하거나 공유 로그에 남기지 않는다.

로그인 후 `GET /api/v1/quiz/categories`, `GET /api/v1/quizzes`, `GET /api/v1/quizzes/{quiz_id}`로 검수 문제를 조회한다. 목록은 기본 limit 20·최대 100이며 반환 cursor를 같은 필터에만 재사용한다. 제출은 새 CSRF와 사용자 범위 UUID `Idempotency-Key`를 포함해 `POST /api/v1/quizzes/{quiz_id}/attempts`에 `selected_option_id`를 보낸다. 동일 키·동일 요청은 같은 결과를 재생하고 다른 요청은 409다.

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

## 서비스별 운영 경로

Python 오프라인 수집은 `python3 scripts/ingest.py list`로 실행한다. 출처·샘플·증분·Wikipedia 이어받기·공식 문서 adapter·재시도·독립 검사는 [수집 안내](runbooks/ingestion.md)를 따른다. 승인 수집 후 `python3 scripts/rag_index.py --index-version <version>`으로 BUILDING Chroma 인덱스를 만들며, 통과한 검색 평가 JSON을 `--activate-evaluation`으로 명시해야 ACTIVE가 된다. `RAG_SERVICE_TOKEN`과 공급자 환경변수를 주입한 뒤 `python3 scripts/rag_service.py --manifest <active-manifest>`로 loopback 내부 API를 실행한다. 결정론 임베딩은 테스트 전용이고 실제 인덱스에는 사용하지 않는다.

동일 collection 증분 동기화는 `scripts/rag_index.py --mode incremental --index-version <version>`을
사용한다. 먼저 `--dry-run`으로 변경·삭제 후보를 확인한다. 삭제는 해당 출처의 무제한 전체 탐색이
오류 없이 완료된 경우에만 `--complete-source <source_id>`를 추가한다. 모델 차원이 바뀌면 기존
collection을 제자리 변경하지 않고 새 index version을 만든다.
스택과 제품 범위는 [ADR 0003](13_PHASE0_DECISIONS.md)으로 확정했다. 아래는 버전·실행 설정 결정 항목이며, 22시간 제한은 적용하지 않는다.
- JDK·Spring Boot·Gradle Wrapper와 포맷·정적 분석 플러그인
- Node·Vue·TypeScript·패키지 매니저·lockfile
- Python·LangChain·의존성 잠금·Ruff·mypy·pytest
- 내부 HTTP API·timeout·오류 계약
- 세션/CSRF·해시·만료 정책의 구현과 모델/임베딩 공급자·호출 제한 ([C02 결정](architecture.md))
- PostgreSQL·ChromaDB 앱 어댑터·마이그레이션·전용 테스트 DB
- 앱 이미지와 Compose 전체 개발 스택

Docker 개발 adapter와 운영 provider 경로를 구분하며 로컬 fixture 결과를 운영 품질 증거로 사용하지 않는다.
공통 명령 설명은 [scripts/README.md](../scripts/README.md), 상태·신뢰 경계는 [하네스 안내](../harness/README.md)를 따른다.

기존 `harness/tasks/001-bootstrap.json`은 이전 RAG 단독 범위다. 신규 학습 기능 실행 전 [하네스 연계](harness-workflow.md)의 task·검사 등록 전환이 필요하다. 현재 명령을 신규 제품 전체 검증으로 보고하지 않는다.

Windows에서 문서·구조 확인만 수행할 때는 `python -X utf8 scripts/check_docs.py`, `python -X utf8 harness/check.py`를 사용할 수 있다. 하네스 회귀·상태 실행기는 POSIX 환경이 필요하다. 서비스 실행 명령·포트·환경변수 템플릿은 실제 bootstrap 후 기록한다.

## 로컬 PostgreSQL·ChromaDB (C03)

Docker Engine + Compose v2 이상이 필요하다. 루트 [.env.example](../.env.example)을 `.env`로 복사하고 개발 전용 POSTGRES_PASSWORD를 채운다. 기존 `backend/.env.example`과 backend 환경은 AI 공급자 설정으로 보존한다. 루트 `.env`를 backend 파일로 덮어쓰거나 실제 비밀값을 커밋하지 않는다. Compose는 루트 `.env`를 자동 로드한다.

```sh
docker compose config --quiet
docker compose up -d --build --wait --wait-timeout 240
docker compose ps
docker compose exec postgres sh -c 'pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
curl --fail http://localhost:8000/api/v2/heartbeat
```

PostgreSQL `postgres:17.9-bookworm`과 Chroma `chromadb/chroma:1.5.3` 공식 이미지를 고정했다. PostgreSQL은 UTF8·UTC 기본값, `/var/lib/postgresql/data` named volume, Chroma는 `/data` named volume과 CHROMA_PERSIST_PATH를 사용한다. DB 이름/사용자/암호는 초기 빈 PostgreSQL 볼륨에서만 적용된다. 이후 `.env` 수정은 기존 계정을 변경하지 않는다. 도메인 테이블·migration은 후속 bootstrap이며 임의 초기 스키마를 생성하지 않는다.

| 실행 위치 | PostgreSQL | ChromaDB |
|---|---|---|
| 개발 호스트 | localhost:POSTGRES_PORT (기본 5432) | CHROMA_HOST=localhost, CHROMA_PORT=8000 |
| Compose data 네트워크 | postgres:5432 | chroma:8000 |

포트 충돌은 루트 `.env`의 공개 포트로 조정한다. 컨테이너 내부 포트는 바뀌지 않는다. AI 컨테이너는 같은 data 네트워크에서 CHROMA_HOST=chroma/CHROMA_PORT=8000을 사용하며 Chroma health를 기다린다. host loopback 공개는 로컬 개발용이며 운영 공개/인증 구성이 아니다.

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
