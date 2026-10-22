# 질문·답변 도메인

상태: Python 검색→생성→인용 ID 검증과 인증된 내부 HTTP, Spring 풀이 문맥 복원·대화/인용 저장, Vue 퀴즈 연계 AS 패널과 대화 목록·복원을 구현했다. 공개 필드 기준은 [API 계약](../api/openapi.yaml), 내부 문맥은 [RAG 계약](../api/internal-rag.md)이다.

C23에서는 외부 RAG 호출 전 USER와 pending ASSISTANT를 커밋하고 호출 중 DB 트랜잭션을 유지하지 않는다. 성공 시 답변과 citation을 한 트랜잭션으로 저장하고, timeout/upstream/저장 오류는 failed 상태로 기록한다. 세션별 UUID Idempotency-Key와 질문 hash로 완료 응답을 재생하며 실패 재시도에서도 USER 메시지를 중복 생성하지 않는다. 목록·상세·메시지 조회는 모든 SQL에서 인증 사용자 소유권을 제한한다.
Spring Boot는 질문 입력 검증과 요청 ID·timeout·오류 변환을 담당한다.
Python은 검색 증거를 바탕으로 답변을 생성하고 출처를 검증한다.
Vue는 질문·로딩·답변·근거 부족·오류·출처를 표시한다.

질문은 본인 chat session에 속한다. Spring은 세션의 본인 attempt_id로 문제·선택·정오답·개념을 복원한다. 이전 대화의 답변은 현재 검색 근거를 대체하지 않는다. 일반 대화는 문제 문맥 없이 지원한다.

## 응답
- answered: 근거에 기반한 answer와 해당 검색 결과에서 확인된 sources.
- insufficient_evidence: 근거 부족 안내. 사실을 추측해 채우지 않는다.
- concept_ids: 이번 질문에서 등록 개념 원장과 매핑한 ID. 일반 대화에서도 관련 문제 생성의 입력으로 사용할 수 있다. 매핑이 없으면 빈 배열이며 생성 전에 등록 개념 선택이 필요하다.
- 400: 입력 검증, 401: 인증, 403: CSRF, 404: 본인 대화 없음, 429: 제한, 500: 저장 실패, 502: RAG 오류, 504: timeout.

모델이 생성한 URL을 그대로 출처로 쓰지 않는다. 검색된 chunk_id를 기준으로 서버가 출처를 구성한다.
인용 ID 존재 여부와 주장-근거 일치는 별도 검사다.
공격 문서가 환경변수·shell·외부 호출을 요구해도 실행하지 않는다.

검사: 입력 길이·빈 입력, 위조 출처 거부, 근거 부족, timeout, UI 상태 전환, 대표 답변 사람 검토.

2026-10-22 GMS `gpt-5-mini` 라이브 답변은 검색된 `POSIX threads`와 `fork` 두 청크 ID만 인용했고 URL은 Chroma 메타데이터에서 구성했다. 존재하지 않는 concept 필터는 `insufficient_evidence`를 반환했다. 전용 로컬 사용자로 Vue proxy→Spring→Python→Chroma/GMS 경로의 오답 제출과 “왜 틀렸어?” 답변·HTTPS 출처 저장을 확인했다. 이 결과는 로컬 fixture 연동 증거이며 승인 코퍼스의 의미 품질 증거는 아니다.
