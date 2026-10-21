# Backend

[작업 안내](AGENTS.md)를 먼저 읽는다.
Java/Spring Boot는 src/에서, Python/LangChain은 ai/에서 독립 프로세스로 구현한다.
JDK 21 / Gradle 8.14.3 / Spring Boot 3.5.16이다. 실행·전용 PostgreSQL 통합 검사는 [개발 안내](../docs/development.md)를 따른다. `./gradlew check bootJar`로 포맷·정적 분석·DB 통합 검사·빌드를 수행한다. 테스트에는 별도의 PostgreSQL DB_URL/DB_USER/DB_PASSWORD가 필요하다. H2와 자동 schema 생성은 사용하지 않는다.
