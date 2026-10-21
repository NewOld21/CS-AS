# ADR 0001: 단일 개발 에이전트와 외부 검증

상태: 하네스 초기 결정

이 문서의 22시간·저장소 추천은 당시 배경 기록이다. 현재 제품 범위·시간 제약·스택은 [ADR 0003](../13_PHASE0_DECISIONS.md)으로 대체한다. 단일 개발 에이전트와 외부 검증 원칙은 유지한다.

22시간 MVP에서 다중 에이전트 운용보다 작업 명세·독립 검증·인계 상태를 먼저 구축한다.
저장소 도구는 검사 실행과 상태 기록을 제공한다. 실제 권한 격리, LLM 비용, GitHub 게시 권한은 외부 관리자가 맡는다.
Spring Boot와 backend/ai의 Python RAG는 API와 프로세스로 분리한다. PostgreSQL + pgvector는 초기 추천이며 서비스 bootstrap 시 확정한다.

참고: https://github.com/revfactory/harness-100 및 https://github.com/revfactory/harness/blob/main/README_KO.md
코드나 템플릿을 복사하지 않고 프로젝트에 맞춰 새로 작성했다. Claude 전용 팀 API에 의존하지 않는다.
