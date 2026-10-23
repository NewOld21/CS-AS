# Current task

현재 작업: [018 C28~C31 학습 이력·오답 복습](exec-plans/active/018-c28-c31-learning-history.md). C28 이력/상세·스냅샷부터 C29 복습·통계, C30 UI, C31 생성 문제 포함 E2E 순서로 구현·검증·개별 커밋한다. 017의 실제 GMS/코퍼스 미검증 사항은 별도로 유지한다.

현재 구현: [017 C24~C27 근거 패널·관련 퀴즈](exec-plans/active/017-c24-c27-evidence-quizzes.md). Citation 본문 snapshot·접근 가능한 패널, 근거 기반 후보 생성·독립 검증·개인 저장·기존 채점과 새로고침 복구를 구현했다. 테스트와 라이브 검증 여부는 해당 계획에서 구분한다.

현재 작업: C21~C23을 완료했으며 다음 구현 범위는 [005 학습 루프 완성](exec-plans/active/005-complete-learning-loop.md)의 복습 상태·학습 이력·관련 문제 생성이다.

최신 완료 마일스톤: [016 C21~C23 운영형 RAG와 사용자 대화 복원](exec-plans/completed/016-c21-c23-operational-rag.md). content hash 기반 증분 인덱싱, 실제 코퍼스 20문항 검색 평가, 사용자별 일반/퀴즈 대화 목록·복원과 멱등·실패 처리를 구현했다. Docker 전체 스택에서 Spring 통합 검사, Vue 단위·브라우저 검사와 실제 RAG E2E를 검증했다.

C22 운영 상태: `csas-live-20261023-v5`는 36문서/1,024청크, `text-embedding-3-large`
3,072차원 ACTIVE 인덱스다. 20문항 문서 평가는 Hit/Recall@1 0.90, @3 0.90, @5 0.95,
MRR 0.9125이며 조건부 HTTP 요청 1문항이 Top-5에서 누락됐다.

최신 완료 마일스톤: [015 승인 출처 라이브 코퍼스와 Docker RAG 전환](exec-plans/completed/015-approved-live-corpus.md). 5개 승인 출처에서 36문서/794 staging 청크를 수집하고 `text-embedding-3-small` 기반 1,024청크 `csas-live-20261023-v4`를 ACTIVE로 전환했다. 5개 검색 probe와 Vue→Spring→Python→Chroma/GMS 퀴즈 오답 E2E가 통과했으며 Docker 전체 스택이 이 인덱스를 사용한다. 다음은 C21 증분 인덱싱과 C22 15~20문항 검색 평가다.

최신 완료 마일스톤: [014 GMS 라이브 RAG 검증](exec-plans/completed/014-gms-live-rag-validation.md). Docker 전체 스택에서 `backend/.env`를 통해 GMS `text-embedding-3-large`(3072차원)와 `gpt-5-mini`를 실제 호출하고 Chroma 적재·검색·인용·근거 부족 및 Vue→Spring→Python 퀴즈 AS E2E를 확인했다. 등록부 81개는 모두 승인 대기라 실제 수집/JSONL은 0건이며, 별도 `csas-gms-live-dev-v1`의 15 fixture 청크를 운영 코퍼스와 구분한다. Python 54개(실제 Chroma 포함)와 Vue 10개가 통과했다.

최신 완료 마일스톤: [008 C18~C20 수집 파이프라인 고도화](exec-plans/completed/008-data-ingestion.md). OSSU 없는 등록부 계약, Wikipedia categorymembers BFS/continuation/영속 이어받기, Retry-After 기반 재시도, 공식 HTML·Markdown·RFC·sitemap adapter와 C15 JSONL 인덱싱 호환을 구현했다. Python은 총 50개 중 49개가 통과했고 실제 Chroma 조건부 1개는 skip했으며, Linux 공통 검증 19개가 통과했다. 81개 출처는 모두 pending·비활성이므로 라이브 본문은 0건이며, RFC/MDN HTTP/PostgreSQL 제한 후보의 이용 조건 승인과 실제 corpus 평가는 후속이다.

최신 완료 마일스톤: [013 C14~C17 Vector 학습 루프](exec-plans/completed/013-c14-c17-vector-learning-loop.md). 수집 JSONL, 구조 청킹·Chroma 인덱스, 근거 답변 내부 API, Spring 문맥 대화와 Vue 퀴즈·AS 화면을 구현했다. Python 41개, 실제 Chroma 통합 1개, Spring/PostgreSQL 35개, Vue 단위 10개와 Playwright UI 8개가 통과했다. 전체 출처 81개가 승인 대기라 실제 문서·운영 청크·외부 LLM 호출은 0이며 ACTIVE 인덱스 품질 평가는 후속이다.

최신 완료: [012 레퍼런스 기반 UI](exec-plans/completed/012-reference-ui.md). 실제 Chrome 레퍼런스 관찰 후 독자적 CS 궤도 지도·Vue 랜딩·인증·본인 계정을 구현했다. 프론트 전체 검사·단위 8개·실제 API 포함 Chrome E2E 8개·Linux 공통 검사를 통과했다. 퀴즈/챗봇/학습 마이페이지는 미구현 상태를 유지하며 [디자인 시스템](design/ui-system.md)에 후속 계획만 기록한다. backend API/DB/인증/RAG는 변경하지 않았다. 다음은 기존 002의 나머지 기반과 004/005 학습 기능이다.

최신 완료: [011 C04~C07 DB migration·사용자 인증](exec-plans/completed/011-c04-c07-auth.md). Spring Boot/Flyway·가입·로그인·세션·로그아웃과 인증 정책을 구현했고 실제 PostgreSQL/HTTP의 17 tests, 포맷·정적 검사·jar 빌드를 통과했다. 세션·CSRF 회전, 유휴/절대 만료, 타인 소유권 거부, 로그아웃 전 쿠키 재전송 401을 확인했다. 실제 학습 기능은 아직 없으며 다음은 002의 남은 서비스 기반이다. 기존 008/002의 미완료 범위는 유지한다.

이전 완료: [009 C02 아키텍처](exec-plans/completed/009-c02-architecture.md), [010 C03 로컬 DB](exec-plans/completed/010-c03-local-db.md). ADR 0004에 따라 PostgreSQL 서비스 DB + ChromaDB 검색 저장소, Spring Security 쿠키 세션을 채택했다. 두 DB의 실제 연결·검색과 restart/down-up 영속성, Linux 공통 검사 19개가 통과했다. 아래 008 수집 작업의 미완료 상태는 유지한다.

다음 작업: review_states·학습 이력과 [005](exec-plans/active/005-complete-learning-loop.md)의 관련 문제 생성을 진행한다.

- 최신 완료: [007 문서 이름·참조 정리](exec-plans/completed/007-document-naming.md). 주 문서를 00~14로 구성하고 링크·진입점·검사·보호 경로를 갱신했다.
- 기준: [PRD](01_PRD.md), [ADR 0003](13_PHASE0_DECISIONS.md), [ADR 0004](decisions/0004-stack.md). 22시간 제한 없이 학습 루프 전체가 1차 목표다.
- 다음 범위: Vue/Python 버전·서비스 골격·내부 계약·프록시·실제 검사 등록. Java 인증/health와 검수 퀴즈 조회·채점·시도 저장은 구현했다. 복습 상태·대화/RAG와 학습 UI는 후속이다.
- 기능 순서: [004 핵심 학습](exec-plans/active/004-core-learning.md) → [005 학습 루프 완성](exec-plans/active/005-complete-learning-loop.md) → [006 Graph 확장](exec-plans/active/006-graph-rag.md).
- 기존 [001 저장소 정리](exec-plans/active/001-repository-structure.md)의 원격 반영 미확인 상태는 유지한다.
- 주의: 기존 machine-readable task와 신규 범위 차이는 [하네스 연계](harness-workflow.md)에서 확인한다.

완료 조건·실제 명령·결과·미해결 항목은 해당 계획에서 관리한다. 실제 실행 로그·재시도 예산·후보 digest는 저장소 밖 state-dir가 기준이며 이 문서에 비밀정보·환경변수·전체 로그를 붙이지 않는다.
