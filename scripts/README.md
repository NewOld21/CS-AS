# 공통 명령

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
