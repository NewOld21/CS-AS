# Backend adapter

루트 AGENTS.md가 공통 진입점이다. 작업 전에 다음을 읽는다.
- [공통 개발 가이드](../docs/08_AGENTS.md)
- [아키텍처](../docs/05_ARCHITECTURE.md)
- [API 계약](../docs/07_API_SPEC.md)
- [답변 도메인](../docs/domain/answering.md)

Java 경로는 src/main/java/com/csas/다. API 입력 검증·유스케이스 조합·RAG 호출·오류 변환을 담당한다.
AI 수정은 [ai/AGENTS.md](ai/AGENTS.md)를 추가로 읽는다. Java에서 Python 모듈을 import하지 않고 내부 HTTP 계약으로 통신한다.
의존성 버전·Gradle Wrapper는 서비스 bootstrap에서 확정한다. 빈 src 구조를 실행 가능한 앱으로 보고하지 않는다.
공통 명령은 [scripts/README.md](../scripts/README.md)를 사용한다.
