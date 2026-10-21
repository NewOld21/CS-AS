# 12. GIT CONVENTION — Git 작업 규칙

상태: 브랜치·커밋·PR 표기 제안. 원격 저장소 설정·브랜치 보호·팀별 승인 정책은 미확정이며 이 문서 작성으로 설정을 변경하지 않는다. 실행 권한과 금지 행동의 기준은 [08_AGENTS](08_AGENTS.md)다.

## 브랜치·커밋 표기

| 구분 | 제안 | 예시 |
|---|---|---|
| 기능 | feat/<작업번호>-<설명> | feat/004-quiz-attempts |
| 수정 | fix/<작업번호>-<설명> | fix/004-attempt-idempotency |
| 문서 | docs/<작업번호>-<설명> | docs/007-document-naming |
| 정리 | refactor/<작업번호>-<설명> | refactor/004-chat-context |

커밋은 `type(scope): 변경 내용` 형식을 기본안으로 삼는다. type은 feat/fix/docs/refactor/test/chore, scope는 auth/quiz/learning/chat/rag/frontend/harness 등 변경 영역을 쓴다. 예: `docs: number project documents and update references`.

독립적으로 검토 가능한 단위로 나누고, 문서/경로 변경은 참조·필수 검사·보호 경로 변경을 같은 변경 단위에 포함한다. 사용자 기존 변경을 임의로 묶어 스테이징하지 않는다. 실제 커밋·원격 쓰기는 해당 작업의 요청 범위에 따라 수행한다.

## PR·검증 기록

PR 설명에는 변경 후 동작과 이유, 연결한 요구사항/작업, 실제 실행한 검사와 결과, 미검증 항목을 적는다. API/DB/화면 변경은 계약·마이그레이션·관찰 가능한 사용자 흐름에 필요한 근거를 포함한다. 문서만 변경했으면 파일/링크/검사 경로 검증으로 범위를 명확히 한다.

커밋/PR 작성은 완료된 로컬 작업을 기록하는 단계이며, 커밋 생성·push·병합을 이 문서가 자동 승인하지 않는다. 브랜치 이름과 기본 브랜치 명칭·병합 방식·승인 인원은 실제 저장소/팀에서 확정한다.

## 관련 기준

[구현 계획](10_IMPLEMENTATION_PLAN.md) · [검증 시나리오](09_TEST_SCENARIO.md) · [책임과 인계](11_TEAM_OWNERSHIP.md) · [현재 작업](current-task.md).
