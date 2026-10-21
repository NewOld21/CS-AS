# Documentation adapter

[공통 개발 가이드](08_AGENTS.md)와 [문서 지도](README.md)를 먼저 읽는다.
공통 개발 규칙은 08_AGENTS.md, 구조는 05_ARCHITECTURE.md, API는 api/openapi.yaml에서 관리한다.
다른 문서는 기준 문서를 링크하고 같은 규칙을 복사하지 않는다.
확정·제안·미구현·미결정 상태를 구분하고 실제로 실행하지 않은 검사를 통과로 표시하지 않는다.
현재 작업은 current-task.md에서 활성 계획으로 연결한다. 계획에 완료 조건·검사 증거·다음 행동을 남긴다.
완료한 계획은 exec-plans/completed/로 이동하고 current-task.md를 다음 계획으로 갱신한다.
공통 검사: `python3 scripts/verify.py` (저장소 루트 기준).
