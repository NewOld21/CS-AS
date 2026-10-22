# Current task

최신 완료 마일스톤: [004 핵심 학습](exec-plans/active/004-core-learning.md)의 C09~C13 정적 문제 은행 구간. 인증 회귀, V3~V5 개념/퀴즈/선택지/시도 스키마, 공식 문서로 검수한 15문항, 인증된 카테고리·목록·상세, 서버 채점과 사용자 범위 DB 멱등성을 구현했다. PostgreSQL 통합 테스트 32개 범위와 Checkstyle을 통과했다. 004의 review_states·대화/Vector RAG가 남아 있어 계획은 active다.

최신 완료: [012 레퍼런스 기반 UI](exec-plans/completed/012-reference-ui.md). 실제 Chrome 레퍼런스 관찰 후 독자적 CS 궤도 지도·Vue 랜딩·인증·본인 계정을 구현했다. 프론트 전체 검사·단위 8개·실제 API 포함 Chrome E2E 8개·Linux 공통 검사를 통과했다. 퀴즈/챗봇/학습 마이페이지는 미구현 상태를 유지하며 [디자인 시스템](design/ui-system.md)에 후속 계획만 기록한다. backend API/DB/인증/RAG는 변경하지 않았다. 다음은 기존 002의 나머지 기반과 004/005 학습 기능이다.

최신 완료: [011 C04~C07 DB migration·사용자 인증](exec-plans/completed/011-c04-c07-auth.md). Spring Boot/Flyway·가입·로그인·세션·로그아웃과 인증 정책을 구현했고 실제 PostgreSQL/HTTP의 17 tests, 포맷·정적 검사·jar 빌드를 통과했다. 세션·CSRF 회전, 유휴/절대 만료, 타인 소유권 거부, 로그아웃 전 쿠키 재전송 401을 확인했다. 실제 학습 기능은 아직 없으며 다음은 002의 남은 서비스 기반이다. 기존 008/002의 미완료 범위는 유지한다.

이전 완료: [009 C02 아키텍처](exec-plans/completed/009-c02-architecture.md), [010 C03 로컬 DB](exec-plans/completed/010-c03-local-db.md). ADR 0004에 따라 PostgreSQL 서비스 DB + ChromaDB 검색 저장소, Spring Security 쿠키 세션을 채택했다. 두 DB의 실제 연결·검색과 restart/down-up 영속성, Linux 공통 검사 19개가 통과했다. 아래 008 수집 작업의 미완료 상태는 유지한다.

현재 추가 작업: [008 CS 데이터 수집](exec-plans/active/008-data-ingestion.md). 오프라인 수집 CLI·출처 81개 등록·모의 샘플·독립 테스트 28개를 구현/검증했다. 전체 출처는 승인 대기·비활성이다. Windows fcntl 부재로 POSIX 공통 검증은 미완료이며 계획을 active에 유지한다. 기존 서비스 bootstrap은 후속이다.

다음 작업: [002 서비스 bootstrap](exec-plans/active/002-service-bootstrap.md) — Java/DB/인증 일부 선행 완료, Vue·Python HTTP·내부 통신·하네스 등록은 미착수.

- 최신 완료: [007 문서 이름·참조 정리](exec-plans/completed/007-document-naming.md). 주 문서를 00~14로 구성하고 링크·진입점·검사·보호 경로를 갱신했다.
- 기준: [PRD](01_PRD.md), [ADR 0003](13_PHASE0_DECISIONS.md), [ADR 0004](decisions/0004-stack.md). 22시간 제한 없이 학습 루프 전체가 1차 목표다.
- 다음 범위: Vue/Python 버전·서비스 골격·내부 계약·프록시·실제 검사 등록. Java 인증/health와 검수 퀴즈 조회·채점·시도 저장은 구현했다. 복습 상태·대화/RAG와 학습 UI는 후속이다.
- 기능 순서: [004 핵심 학습](exec-plans/active/004-core-learning.md) → [005 학습 루프 완성](exec-plans/active/005-complete-learning-loop.md) → [006 Graph 확장](exec-plans/active/006-graph-rag.md).
- 기존 [001 저장소 정리](exec-plans/active/001-repository-structure.md)의 원격 반영 미확인 상태는 유지한다.
- 주의: 기존 machine-readable task와 신규 범위 차이는 [하네스 연계](harness-workflow.md)에서 확인한다.

완료 조건·실제 명령·결과·미해결 항목은 해당 계획에서 관리한다. 실제 실행 로그·재시도 예산·후보 digest는 저장소 밖 state-dir가 기준이며 이 문서에 비밀정보·환경변수·전체 로그를 붙이지 않는다.
