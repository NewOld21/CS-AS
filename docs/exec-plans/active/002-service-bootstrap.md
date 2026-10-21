# 002 서비스 bootstrap

Status: planned

## 목표·범위

현재 골격에 Vue/TypeScript·Spring Boot·별도 Python/LangChain 서비스와 PostgreSQL/pgvector 개발 환경을 생성한다. 기준은 [ADR 0003](../../13_PHASE0_DECISIONS.md)과 [PRD](../../01_PRD.md)다. 22시간 제한은 없다.

선행: 003 설계 검토. 001의 원격 반영 미확인 이력은 유지한다. 이 계획은 로컬 구현 기반 작업이며 원격 게시를 포함하지 않는다.

수정 범위: backend/, frontend/, docs/. task·검사 등록과 하위 AGENTS의 제품 경로 정렬은 이유·검사를 명시한 별도 검토 가능한 변경 단위로 수행한다. Graph·업무 기능 전체·운영 배포는 제외한다. 인증 구현 자체는 004이며 여기서는 세션/CSRF 구성 기반과 계약을 고정한다.

## 완료 조건

- [ ] JDK/Spring Boot/Gradle·Node/Vue/TypeScript·Python/LangChain·PostgreSQL/pgvector 버전과 lockfile/Wrapper 고정.
- [ ] 세 서비스 health·프록시·내부 통신·서비스 인증·timeout/deadline·오류 매핑 확인.
- [ ] 공개 OpenAPI·내부 RAG DTO와 상태별 응답 계약 검사.
- [ ] 세션/CSRF·암호 해시·만료·로컬/운영 쿠키 설정·호출 제한 정책 결정.
- [ ] ERD migrations 기반·전용 PostgreSQL/pgvector 테스트 DB 구성.
- [ ] Java/Vue/Python 포맷·정적 검사·테스트·빌드 명령 등록.
- [ ] 신규 학습 task와 추가 검사 등록 계획 반영. 기존 task를 신규 제품 전체 기준으로 사용하지 않음.
- [ ] development/testing을 실제 실행 명령과 결과로 갱신.

## 검증·인계

현재 미실행이다. 기존 machine-readable task는 [하네스 연계](../../harness-workflow.md)의 전환 항목을 확인한 뒤 사용한다. 서비스 기반 완료는 1차 제품 완료와 다르다. 기능 검사는 004/005까지 계속 확장한다.

실제 명령·결과·버전·미해결 항목을 남긴 뒤 completed/로 이동한다. 다음은 [004 핵심 학습](004-core-learning.md)이다.
