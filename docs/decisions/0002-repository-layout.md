# ADR 0002: 문서와 영역별 진입점

상태: 채택

## 배경
참고 저장소 MAIRRY처럼 공통 안내·영역별 책임·API·검사 경로를 분리하고 사용자가 제시한 docs 구조를 적용한다.
참고: https://github.com/SSA-FARI/MAIRRY (구조를 참고하며 도메인이나 코드를 복사하지 않는다).

## 결정
- 공통 규칙은 docs/08_AGENTS.md에 한 번만 작성한다.
- 루트·backend·backend/ai·frontend·docs에 AGENTS.md를 둔다.
- Python RAG는 backend/ai에 두고 Java와 별도 프로세스로 실행한다.
- docs/domain은 orders/payments 예시 대신 ingestion/retrieval/answering으로 나눈다.
- 공개 API는 docs/api/openapi.yaml로 이동한다.
- scripts/는 공통 명령, harness/는 실행 엔진과 평가·정책을 담당한다.
- current-task는 active 계획에 연결한다. 완료 증거가 있는 계획만 completed로 이동한다.

## 영향·검증
기존 backend/ai/ 경로와 API 경로 참조를 갱신한다. 문서 링크·필수 파일·하네스 회귀 검사로 연결을 확인한다.
기술 버전과 앱 코드는 별도 서비스 bootstrap task로 남긴다.
