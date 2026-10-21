# Frontend adapter

[공통 개발 가이드](../docs/08_AGENTS.md), [제품 개요](../docs/00_PROJECT_PROPOSAL.md),
[API 계약](../docs/07_API_SPEC.md), [답변 도메인](../docs/domain/answering.md)을 읽는다.

Vue/TypeScript는 src/app/·src/domains/·src/shared/로 나눈다. 공개 Spring Boot API만 호출한다.
AI 키·DB 접속정보를 번들에 포함하지 않는다. 답변은 텍스트 렌더링을 기본으로 하고 출처 URL을 검사한다.
로딩·빈 결과·근거 부족·입력 오류·시간 초과 상태를 구분한다.
버전·패키지 매니저·lockfile·빌드 명령은 서비스 bootstrap에서 확정한다.
검사 경로는 [scripts/README.md](../scripts/README.md)다.
