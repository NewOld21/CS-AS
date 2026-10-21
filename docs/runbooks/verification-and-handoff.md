# 검증 실패와 작업 인계

1. state-dir의 state.json, reports/, events.jsonl과 task 완료 조건을 확인한다.
2. 실패를 코드·환경·외부 서비스·정책으로 분류한다. 원인 가설·시도·다음 행동은 notes.md에 적는다.
3. 수정 후 관련 검사 → 전체 검사 순으로 수행한다.
4. blocked이면 새 run으로 한도를 초기화하지 않고 인간에게 인계한다.
5. `python3 scripts/task.py handoff --state-dir /path/to/run`으로 실행 상태 인계를 갱신한다.
6. 외부 관리자가 변경 patch·미추적 파일 snapshot·코퍼스 manifest·모델/인덱스 버전을 보존한다.

run.py는 전체 workspace나 DB를 백업하지 않는다. 복원 시 기준 commit과 후보 digest를 확인한다.
SIGKILL 등으로 running 상태가 남으면 다음 검증에서 blocked로 전환한다.
상태 파일을 수동으로 초기화해 성공으로 바꾸지 않는다.

하네스 green은 서비스 통과가 아니다. [테스트 수준](../09_TEST_SCENARIO.md)을 확인한다.
