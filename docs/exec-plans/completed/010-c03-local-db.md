# 010 C03 PostgreSQL·ChromaDB 로컬 환경

Status: completed

## 범위·완료 조건

사용자 C03 요청. allowed_paths: compose.yaml, .env.example, .gitattributes, scripts/, docs/. .gitattributes는 Windows checkout에서도 컨테이너용 shell probe의 LF를 보존하기 위해 추가한다. 기존 backend/.env.example은 보존하고 backend/.env는 읽거나 변경하지 않는다. 운영 배포·전체 RAG 구현·임베딩 모델 적용은 제외한다.

- [x] 공식 버전 고정 이미지, loopback 포트, named volumes, health checks.
- [x] PostgreSQL 실제 SQL 및 Python Chroma HttpClient 읽기·쓰기·검색.
- [x] restart와 down/up 후 양쪽 데이터 보존. 기존 볼륨·데이터 삭제 금지.
- [x] 실행·초기화 안내, 공통 검사, 독립 커밋과 증거.

## Baseline

Docker 29.7.2 / Compose v5.4.0. sandbox Docker pipe 접근은 제한되어 승인된 Docker 명령으로 진행한다. 호스트 자격증명 대신 빈 `reports/docker-config`를 사용한다. POSIX 하네스의 Windows fcntl 오류는 기존 환경 제한이다.

## 실행 증거 (2026-10-21)

환경: Windows PowerShell, Python 3.12.10, Linux Docker Engine 29.7.2, Compose v5.4.0. C02 커밋 d692602에 C03 파일을 추가했다. 실제 루트 `.env`에는 새 로컬 전용 난수 암호만 생성했으며 Git 제외다. backend 환경 파일은 변경하지 않았다.

| 검사 | 실제 결과 |
|---|---|
| `docker --config reports/docker-config compose config --quiet` | exit 0 |
| `docker --config reports/docker-config compose up -d --wait --wait-timeout 120` | exit 0, postgres/chroma healthy |
| `.venv/Scripts/python -X utf8 scripts/check_local_db.py write --state reports/local-db-smoke.json --docker-config reports/docker-config` | exit 0, SQL UTF8 한글 쓰기/읽기와 Chroma heartbeat/get/vector query PASS |
| `compose restart`, `compose up -d --wait`, 같은 state의 `read` | 모두 exit 0, 양쪽 동일 데이터 유지 |
| `compose down`, `compose up -d --wait`, 같은 state의 `read` | 모두 exit 0, 양쪽 동일 데이터 유지, volumes 옵션 미사용 |
| TCP 127.0.0.1 + PGPASSWORD로 최종 SQL read | exit 0, 실제 암호 인증 연결 |
| `python -X utf8 -m unittest discover -s backend/ai/tests -p 'test_*.py' -q` | exit 0, 28 tests PASS |
| Windows `PYTHONUTF8=1 python scripts/verify.py` | exit 1: 문서/구조 PASS, 기존 fcntl 부재 |
| Linux `python:3.12.10-slim`의 `python scripts/verify.py` (소스 readonly mount) | exit 0: 문서/구조 + 하네스 19 tests PASS |

일반 환경에서는 `--config reports/docker-config` 없이 같은 명령을 사용한다. 이 실행에서는 호스트 자격증명을 읽지 않기 위해 Compose 실행 파일 경로만 별도 Docker 설정에 지정했다. 검증용 새 컬렉션·테이블만 cleanup으로 정리하고 두 서비스는 실행 상태로 남긴다. 검증 클라이언트 전체 설치 버전은 requirements-local-db.lock.txt에 기록한다.

### 교정 기록

최초 공식 예시의 curl probe는 실제 Rust 이미지에 curl이 없어 실패했다. Bash가 포함됨을 확인해 HTTP 상태를 검사하는 readonly probe로 교정하고 healthy를 확인했다. SDK는 현재 디렉터리 `.env`를 자동 해석하며 추가 Compose 키를 거부했다. 빈 임시 디렉터리 import와 `_env_file=None`으로 분리한 뒤 smoke가 성공했다. 임베딩 모델·실제 출처 수집·RAG 서비스 구현은 수행하지 않았다. 별도 shell OpenAPI 검사 인용 실패는 JSON 구조 검사로 재확인한다.

## 다음 작업

최종 OpenAPI JSON 로컬 `$ref` 전체 해석과 오류 필수 필드 검사: exit 0. cleanup: exit 0. PostgreSQL과 Chroma 모두 최종 healthy 상태다.

검증한 이미지 digest:
- PostgreSQL: `sha256:47f917f7409eacd22fc5dfb1dee634e1b55cf0c01d1a7eb701be2227a03e0641`
- Chroma: `sha256:cfd193653bd61076610730a09acae34ab85b5b6b1f5db4d944c17b5e8453658d`

[002 bootstrap](../active/002-service-bootstrap.md): 앱 버전/lockfile, 서비스 통신·인증 구현, 도메인 migration, 실제 RAG 어댑터와 평가. 기존 008의 미완료 라이브 수집/승인 상태는 유지한다. 로컬 smoke는 실제 검색 품질·서비스 full 검증을 대체하지 않는다.
