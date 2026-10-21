# 공통 명령

Java 앱과 전용 PostgreSQL 통합 검사: `python scripts/backend.py up`, `python scripts/backend.py check`. Docker 설정 파일 접근이 제한된 환경은 `--docker-config /path/to/config`를 선택할 수 있다. 실행·CSRF·쿠키·DB 구분은 [개발 안내](../docs/development.md)를 따른다. 기존 공통 하네스와 Java 검사는 별개이며 full 등록은 후속 하네스 변경 작업이다.

저장소 루트 기준. Python 3.11+, Linux/POSIX 환경을 사용한다.

```sh
# 문서·하네스 구조와 회귀 검사
python3 scripts/verify.py
# 문서 구조·내부 링크만 검사
python3 scripts/check_docs.py
# 실행 상태 생성: 저장소 밖의 영속 경로 권장
python3 scripts/task.py init --state-dir /tmp/csas-run --task harness/tasks/001-bootstrap.json
# 상태가 있는 검증/인계
python3 scripts/task.py verify --state-dir /tmp/csas-run --profile bootstrap
python3 scripts/verify.py --profile full --state-dir /tmp/csas-run
python3 scripts/task.py handoff --state-dir /tmp/csas-run
```

verify.py는 기존 harness 엔진을 호출하는 공통 진입점이다. 엔진을 중복 구현하지 않는다.
full은 현재 미구현 항목 때문에 실패한다. bootstrap 성공으로 서비스 완료를 선언하지 않는다.
보안 집행·모델 비용·운영 권한은 별도 실행 관리자 영역이다. [하네스 안내](../harness/README.md)를 참고한다.

로컬 DB의 실제 SQL·Chroma Python 클라이언트 검사는 `check_local_db.py write|read|cleanup --state reports/local-db-smoke.json`을 사용한다. 전용 가상환경에 requirements-local-db.lock.txt를 설치한다. health·restart·down/up 절차는 [개발 안내](../docs/development.md)를 따른다. 이 검사는 공통 하네스 full 또는 실제 RAG 품질 검사를 대체하지 않는다.
