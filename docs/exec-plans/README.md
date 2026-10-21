# Execution Plans

- active/: 진행 중인 작업과 다음 계획. 각 파일에 status를 명시한다.
- completed/: 완료 조건과 검증 증거가 확인된 계획만 이동한다.
- [template.md](template.md)를 복사해 번호·목표·범위·선행 조건·완료 조건·검사·인계를 작성한다.
- [current-task.md](../current-task.md)는 현재 진행 중인 계획 하나를 가리킨다.
- machine-readable 작업·검사 정책은 harness/에서 관리한다. 실제 상태는 저장소 밖 영속 state-dir에 둔다.
