# 05. ARCHITECTURE — 서비스·프로젝트 구조

상태: C04~C13의 인증·정적 퀴즈·채점에 이어 C14~C17의 수집 JSONL, 버전별 Chroma 인덱싱, Python 내부 답변 API, Spring 대화 저장/문맥 복원, Vue 퀴즈·AS 화면을 구현했다. 실제 승인 코퍼스·ACTIVE 인덱스·외부 모델 자격증명은 아직 공급하지 않았으므로 운영 RAG 활성화와 품질 평가는 남아 있다. Vue + Spring Boot + Python RAG + PostgreSQL + ChromaDB 경계는 유지한다.

## 서비스 경계

Vue → Spring Boot 공개 API → Python RAG 내부 API → ChromaDB/모델 공급자.
Spring은 PostgreSQL 서비스 스키마를 통해 사용자·퀴즈·학습 기록을 관리한다. Python은 ChromaDB의 검색용 문서·청크·임베딩을 관리하며 사용자 계정·채점 테이블을 수정하지 않는다.

수집은 별도 승인 출처 파이프라인이다. 사용자 질문이 임의 URL 수집을 유발하지 않는다. Python은 backend/ai/에 두고 Java와 별도 프로세스·이미지·의존성으로 실행한다.

## 디렉터리와 책임

| 경로 | 책임 |
|---|---|
| backend/src/main/java/com/csas/common/ | 설정·공통 오류·현재 사용자 타입 |
| backend/src/main/java/com/csas/application/ | 도메인 유스케이스 조합·트랜잭션 |
| backend/src/main/java/com/csas/domains/auth/ | 가입·인증·세션 |
| backend/src/main/java/com/csas/domains/quiz/ | 문제·선택지·서버 채점·발행 제약 |
| backend/src/main/java/com/csas/domains/learning/ | 풀이·멱등성·복습 상태·통계 |
| backend/src/main/java/com/csas/domains/chat/ | 대화·메시지·본인 풀이 문맥 |
| backend/src/main/java/com/csas/domains/concept/ | 공통 개념 ID·별칭·분야 |
| backend/src/main/java/com/csas/domains/generation/ | 생성 요청·검증 기록·개인 문제 저장 |
| backend/src/main/java/com/csas/integrations/rag/ | 내부 RAG HTTP 클라이언트 |
| backend/src/main/resources/db/migration/ | 버전 있는 DB 변경 |
| backend/src/test/java/com/csas/ | Java 계약·회귀·통합 검사 |
| backend/ai/src/csas_rag/api/ | 내부 요청·응답 검증 |
| backend/ai/src/csas_rag/ingestion/ | 수집·정제·청킹·개념 매핑·적재 |
| backend/ai/src/csas_rag/retrieval/ | 검색 인터페이스·질의·근거 선택 |
| backend/ai/src/csas_rag/generation/ | 답변 생성·인용 검증 |
| backend/ai/src/csas_rag/generation/quiz/ | 퀴즈 후보 생성·독립 검증 |
| backend/ai/src/csas_rag/providers/ | 모델·임베딩·ChromaDB 어댑터 |
| backend/ai/tests/ | 검색·생성·출처·공격 문서·실제 코퍼스 평가 |
| frontend/src/app/ | 라우팅·인증 가드·학습 화면 전환 |
| frontend/src/domains/auth/ | 가입·로그인·인증 상태 |
| frontend/src/domains/quiz/ | 문제·제출·해설·생성 문제 |
| frontend/src/domains/chat/ | 문제 문맥·대화·메시지 |
| frontend/src/domains/source/ | 출처 타입·표시 |
| frontend/src/domains/learning/ | 마이페이지·이력·오답·재풀이 |
| frontend/src/domains/concept/ | 개념 표시·추후 지식 지도 |
| frontend/src/shared/ | 도메인 지식 없는 공통 UI·API transport |
| frontend/tests/unit/, frontend/tests/e2e/ | 상태·컴포넌트·학습 루프 검사 |
| docs/, scripts/, harness/ | 제품/설계 기준, 공통 실행 명령, 검증 엔진/정책/평가셋 |

기존 question 경로는 초기 골격이다. bootstrap에서 질문 유스케이스를 chat에 정리하고 동일 질문 처리기를 중복 구현하지 않는다. 기존 경로 제거/이동은 실제 코드 생성 작업에서 검사와 함께 수행한다.

## 의존 규칙

- Controller → Application/Service → Repository/외부 어댑터 순서다. 도메인 간 Repository 직접 참조 대신 공개 조회 인터페이스를 사용한다.
- application이 Quiz·Learning을 조합해 채점·시도·복습을 한 트랜잭션으로 묶는다. Chat은 본인 풀이 문맥 조회를 사용하고 클라이언트 채점값을 신뢰하지 않는다.
- common/shared는 도메인 모듈을 역참조하지 않는다. Vue는 공개 API만 호출하며 DB·Python을 직접 호출하지 않는다.
- Vue app이 quiz→chat→learning 전환을 조합한다. 각 domain은 공개 타입/동작을 노출하고 다른 domain의 화면 내부 구현을 직접 import하지 않는다.
- Python은 Java 코드를 import하지 않는다. 모델·Vector DB SDK는 providers에 격리한다. 실제 보안 집행은 런타임/외부 실행 관리자가 담당한다.

## Graph 확장 지점

1차에는 VectorRetriever를 사용한다. 2차에 retrieval/graph.py·providers/graph/와 Java integrations/graph/·concept 관계 조회를 추가할 수 있다. HybridRetriever가 Vector·Graph 결과를 같은 근거 타입으로 반환하도록 한다. 실제 경로와 Neo4j 의존성은 Graph 작업에서 생성한다.

개념 식별자는 PostgreSQL concepts 원장이 관리한다. 퀴즈·문서·학습 이력은 같은 ID를 사용하며, Graph 도입으로 기존 키를 교체하지 않는다. [관계 모델](domain/knowledge-graph.md)에 근거·검증·버전·복구 방식을 정의한다.

## 계약과 버전

[ERD](06_ERD.md) · [RAG 아키텍처](14_RAG_GUIDE.md) · [공개 API](api/openapi.yaml) · [내부 RAG API](api/internal-rag.md).

source_id/document_id/revision/chunk_id, 코퍼스 manifest, 개념 매핑, 임베딩 모델/차원·청크 설정·인덱스 버전을 보존한다. 검증 전 기존 인덱스를 삭제하지 않는다. Java 인증 HTTP와 Python ingestion 오프라인 CLI는 구현되었다. Python HTTP·실제 검색 어댑터는 후속이다. [수집 계약](domain/ingestion.md)에 책임·저장·확장 경계를 정의한다. 파일 객체와 SQLite catalog는 배치 staging이며 PostgreSQL + ChromaDB를 대체하지 않는다.

C02 결정과 API·인증 규칙은 [MVP 아키텍처](architecture.md), pgvector 선택의 변경 근거는 [ADR 0004](decisions/0004-stack.md)를 따른다.
