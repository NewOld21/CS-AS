# Current task

현재 우선 작업: [011 C04~C07 DB migration·사용자 인증](exec-plans/active/011-c04-c07-auth.md). C04부터 순서대로 구현·통합 검사·커밋한다. 기존 008/002의 미완료 범위는 유지한다.

최신 완료: [009 C02 아키텍처](exec-plans/completed/009-c02-architecture.md), [010 C03 로컬 DB](exec-plans/completed/010-c03-local-db.md). ADR 0004에 따라 PostgreSQL 서비스 DB + ChromaDB 검색 저장소, Spring Security 쿠키 세션을 채택했다. 두 DB의 실제 연결·검색과 restart/down-up 영속성, Linux 공통 검사 19개가 통과했다. 다음 구현은 [002 서비스 bootstrap](exec-plans/active/002-service-bootstrap.md)이다. 아래 008 수집 작업의 미완료 상태는 유지한다.

현재 추가 작업: [008 CS 데이터 수집](exec-plans/active/008-data-ingestion.md). 오프라인 수집 CLI·출처 81개 등록·모의 샘플·독립 테스트 28개를 구현/검증했다. 전체 출처는 승인 대기·비활성이다. Windows fcntl 부재로 POSIX 공통 검증은 미완료이며 계획을 active에 유지한다. 기존 서비스 bootstrap은 후속이다.

다음 작업: [002 서비스 bootstrap](exec-plans/active/002-service-bootstrap.md) — Status: planned (미착수).

- 최신 완료: [007 문서 이름·참조 정리](exec-plans/completed/007-document-naming.md). 주 문서를 00~14로 구성하고 링크·진입점·검사·보호 경로를 갱신했다.
- 기준: [PRD](01_PRD.md)와 [ADR 0003](13_PHASE0_DECISIONS.md). 기존 스택 유지, 22시간 제한 없이 학습 루프 전체가 1차 목표다.
- 다음 범위: 버전·서비스 골격·공개/내부 계약·인증 구성 기반·전용 DB·실제 검사 등록. 현재 서비스 구현은 없다.
- 기능 순서: [004 핵심 학습](exec-plans/active/004-core-learning.md) → [005 학습 루프 완성](exec-plans/active/005-complete-learning-loop.md) → [006 Graph 확장](exec-plans/active/006-graph-rag.md).
- 기존 [001 저장소 정리](exec-plans/active/001-repository-structure.md)의 원격 반영 미확인 상태는 유지한다.
- 주의: 기존 machine-readable task와 신규 범위 차이는 [하네스 연계](harness-workflow.md)에서 확인한다.

완료 조건·실제 명령·결과·미해결 항목은 해당 계획에서 관리한다. 실제 실행 로그·재시도 예산·후보 digest는 저장소 밖 state-dir가 기준이며 이 문서에 비밀정보·환경변수·전체 로그를 붙이지 않는다.
