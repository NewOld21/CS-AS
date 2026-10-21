# ADR 0004: MVP 스택·인증과 로컬 ChromaDB 채택

Status: Accepted (2026-10-21). C02 결정. [ADR 0003](../13_PHASE0_DECISIONS.md)의 VectorDB 선택과 인증 기본안을 부분 대체한다. 기존 0001/0002/0003의 식별자와 과거 기록을 보존한다.

## Context

기존 설계는 Vue + Spring Boot + 별도 Python/LangChain + PostgreSQL/pgvector였다. 현재 서비스·migration·검색 어댑터는 없고 오프라인 파일/SQLite 수집 staging만 구현되어 있다. 이번 사용자 요청은 로컬 DB로 PostgreSQL과 ChromaDB를 명시했다. 기존 사용자 변경 `backend/.env.example`은 AI 공급자 설정이므로 수정하지 않는다.

## Decision

| 영역 | 채택 |
|---|---|
| Frontend | Vue.js + TypeScript |
| Backend | Java + Spring Boot |
| AI/RAG | 별도 Python + LangChain 프로세스 |
| Service DB | PostgreSQL |
| VectorDB | ChromaDB |
| Local infrastructure | Docker Compose, 공식 이미지의 명시 버전 |
| Authentication | Spring Security + 서버 쿠키 세션, CSRF, BCrypt |

서비스 책임·API 오류·보안 상세는 [MVP 아키텍처](../architecture.md), 실제 이미지와 접속 설정은 [개발 안내](../development.md)가 기준이다. 버전/lockfile은 생성하는 인프라·검증 클라이언트에만 고정하고 미구현 앱의 빌드 파일은 만들지 않는다.

## Alternatives

- pgvector: 단일 DB의 SQL·트랜잭션·운영 도구를 공유할 수 있다. 이번 명시 요청에 따라 로컬에서는 선택하지 않는다.
- ChromaDB: Python HttpClient와 독립 컬렉션으로 인덱스 실험을 분리할 수 있다. DB 2개의 운영·백업과 manifest 기반 참조 검증 비용이 추가된다.
- JWT: 모바일/다중 서비스에 유리하지만 현재 동일 출처 웹 MVP에서는 토큰 보관·갱신·폐기 구현 비용이 크다. 기존 세션 기본안을 확정한다.

## Consequences

PostgreSQL은 계정·개념·학습 데이터의 원장, Chroma는 검색 projection이다. 기존 pgvector 전용 RAG 테이블은 현재 물리 migration으로 만들지 않는다. 모델/차원/청크 설정별 컬렉션·manifest를 분리하고 검증 후 ACTIVE 포인터를 바꾼다. 문서/청크 ID와 과거 인용 스냅샷을 유지한다. 향후 pgvector 전환은 Retriever/provider 어댑터와 재인덱싱·실제 코퍼스 평가로 진행하며 기존 인덱스를 검증 전에 삭제하지 않는다. 성능 우위는 아직 측정하지 않았다.

## Validation

C02는 OpenAPI 참조·문서 링크·현재 설계의 저장소 일치를 검사한다. C03는 별도 계획에서 health·SQL 읽기/쓰기·Python 클라이언트 검색·재시작 및 down/up 영속성을 검사한다. 설정 검증과 실제 실행 검증을 구분하며 [현재 계획](../current-task.md)에 결과를 남긴다.
