# CS/AS 문서 지도

주 문서는 00~14 순서로 읽는다. 기존 설계 내용은 새 파일명으로 이동하고 상세 계약·도메인·실행 기록은 지원 자료로 유지한다. Java health·migration·인증, 로컬 DB, Vue 소개·인증 UI는 구현했으며 실제 학습 기능·Python HTTP는 후속이다. 문서의 확정·제안·미결정 상태를 구분한다.

| 번호 | 문서 | 내용 |
|---|---|---|
| 00 | [PROJECT PROPOSAL](00_PROJECT_PROPOSAL.md) | 서비스 제안·문제·대상·차별점 |
| 01 | [PRD](01_PRD.md) | 제품 요구사항·기능 ID·정책·수용 기준 |
| 02 | [MVP SCOPE](02_MVP_SCOPE.md) | 1차 전체 학습 루프·2차 확장·제외 범위 |
| 03 | [USER FLOW](03_USER_FLOW.md) | 가입→퀴즈→질문→추가 문제→복습 |
| 04 | [SCREEN SPEC](04_SCREEN_SPEC.md) | 화면별 접근·표시·행동·오류/빈 상태 |
| 05 | [ARCHITECTURE](05_ARCHITECTURE.md) | 서비스·디렉터리 책임·의존 방향 |
| 06 | [ERD](06_ERD.md) | 데이터 모델·관계·트랜잭션·버전 |
| 07 | [API SPEC](07_API_SPEC.md) | 인증·문제·채점·대화·생성·학습 API 안내 |
| 08 | [AGENTS](08_AGENTS.md) | 공통 개발·권한·검증·에이전트 규칙 |
| 09 | [TEST SCENARIO](09_TEST_SCENARIO.md) | 계약·통합·E2E·RAG 품질·검증 증거 |
| 10 | [IMPLEMENTATION PLAN](10_IMPLEMENTATION_PLAN.md) | 단계별 구현 순서·계획·완료 조건 |
| 11 | [TEAM OWNERSHIP](11_TEAM_OWNERSHIP.md) | 영역별 책임·공동 변경·인계 |
| 12 | [GIT CONVENTION](12_GIT_CONVENTION.md) | 브랜치·커밋·PR 표기 제안 |
| 13 | [PHASE0 DECISIONS](13_PHASE0_DECISIONS.md) | 사용자 확정 선택·설계 기본안·미결정 |
| 14 | [RAG GUIDE](14_RAG_GUIDE.md) | Vector RAG·문제 문맥·생성·Graph 확장 |

## 작업·상세 자료

- [AGENTS.md](AGENTS.md)는 문서 영역의 자동 탐색 진입점이며 공통 규칙은 08_AGENTS.md에만 둔다.
- [현재 작업](current-task.md)·[개발 명령](development.md)·[하네스 연계](harness-workflow.md).
- API 상세: [OpenAPI](api/openapi.yaml)·[내부 RAG](api/internal-rag.md)·[2차 Graph API 후보](api/graph-rag.md).
- 도메인: [학습](domain/learning.md)·[생성 검증](domain/quiz-generation.md)·[지식 관계](domain/knowledge-graph.md)·[수집](domain/ingestion.md)·[검색](domain/retrieval.md)·[답변](domain/answering.md).
- [출처 등록부](data-sources.json): 현재 모두 비활성, 이용 조건 검토 후 활성화.
- [결정 이력](decisions/README.md)·[실행 계획](exec-plans/README.md)·[검증/인계 절차](runbooks/README.md).

팀 인원·개인 배정과 Git 운영 설정은 미확정이다. 번호 문서의 제안이 실제 팀 구성이나 원격 설정 변경을 뜻하지 않는다.

C02의 [MVP 아키텍처·API 규칙](architecture.md)과 [스택 ADR 0004](decisions/0004-stack.md)를 현재 결정으로 따른다.
