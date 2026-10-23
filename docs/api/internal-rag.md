# 내부 RAG HTTP 계약

상태: `/internal/v1/answers`와 Spring 클라이언트 구현. `/internal/v1/quiz-candidates`는 제안 상태다. Spring Boot → Python 전용이며 공개 API가 아니다. 답변 경로는 버전·DTO·deadline·서비스 Bearer 인증과 오류 변환을 검사한다.

## 공통

- readiness: `GET /health`는 `{"status":"UP","index_version":"..."}`만 반환하며 자격증명·provider 상세를 노출하지 않는다.
- 경로: `/internal/v1/answers`, `/internal/v1/quiz-candidates` (POST).
- 헤더: `X-Request-Id`, `Authorization: Bearer <runtime-service-token>`. 실제 비밀값은 문서에 넣지 않는다.
- 본문: `deadline_at`(UTC ISO 8601), `index_version`(명시한 ACTIVE 버전), 요청별 입력.
- 인증은 서비스 간 자격증명으로 검증한다. 사용자 쿠키를 Python으로 전달하지 않는다.
- Python은 입력 크기와 남은 deadline을 검사한다. 모델/검색의 재시도 횟수·timeout은 설정으로 고정하고 상위 deadline을 넘지 않는다.
- 오류: 400 INVALID_INPUT, 401 SERVICE_UNAUTHORIZED, 409 INDEX_VERSION_UNAVAILABLE, 502 PROVIDER_FAILED, 504 DEADLINE_EXCEEDED. 본문은 request_id/code/message/timestamp(UTC ISO 8601)다.

## 답변

```json
{
  "request_id": "req-example",
  "deadline_at": "2026-10-21T04:01:00Z",
  "index_version": "cs-v1",
  "question": "왜 틀렸어?",
  "history": [{"role": "user", "content": "인덱스를 공부하고 있어"}],
  "quiz_context": {
    "quiz_id": "00000000-0000-4000-8000-000000000001",
    "attempt_id": "00000000-0000-4000-8000-000000000002",
    "stem": "인덱스의 단점으로 적절한 것은?",
    "options": [{"id": "option-example", "text": "변경 시 유지 비용 발생"}],
    "selected_option_id": "selected-example",
    "correct_option_id": "option-example",
    "is_correct": false,
    "explanation": "데이터 변경 시 관련 인덱스 유지 비용이 발생할 수 있습니다.",
    "concept_ids": ["concept:database-index"]
  }
}
```

예시는 문맥 필드 설명용으로 선택지를 축약했다. 실제 options는 저장된 선택지 4개이고 selected/correct ID는 그 안에 있어야 한다. 일반 대화는 quiz_context=null, history는 서버가 소유권 확인 후 길이를 제한한 최근 USER/ASSISTANT 대화다. 시스템 프롬프트를 사용자 이력으로 받지 않는다.

200 응답:

```json
{
  "request_id": "req-example",
  "status": "answered",
  "concept_ids": ["concept:database-index"],
  "answer": "데이터를 변경할 때 인덱스도 유지해야 하므로 비용이 발생할 수 있습니다.",
  "retrieved_chunks": [{
    "source_id": "approved-source",
    "document_id": "doc-index",
    "revision": "revision-example",
    "chunk_id": "chunk-index-1",
    "title": "인덱스 유지 비용",
    "url": "https://example.com/cs/index",
    "locator": "section:maintenance"
  }],
  "cited_chunk_ids": ["chunk-index-1"],
  "index_version": "cs-v1",
  "model_version": "pinned-at-bootstrap",
  "prompt_version": "answer-v1"
}
```

예시 URL은 실제 승인 출처가 아니다. retrieved_chunks는 생성기에 실제 제공한 근거만 반환한다. Spring은 cited_chunk_ids가 그 집합에 속하는지 확인하고 출처를 조립한다. Python은 그 전에 주장과 근거의 일치를 검사한다. `insufficient_evidence`는 answer=null, cited_chunk_ids=[]이며 오류와 구분한다. 공개 응답에는 사용한 sources만 포함한다.

concept_ids는 이번 질문에서 확인한 등록 개념 ID이며 Spring이 원장 존재를 재검증한다. 일반 대화의 관련 문제 생성에도 사용한다. 원장 매핑이 없으면 빈 배열이다. 검색 문서에 단순히 나타난 모든 개념을 학습 개념으로 반환하지 않는다.

## 퀴즈 후보 생성·검증

입력: 공통 필드 + `concept_ids`, `difficulty`, 선택적 `learning_context`(정규화된 개념 설명, 최근 사용자 질문), `exclude_quiz_fingerprints`(서버 제한 길이). 소유자 식별정보는 보내지 않는다.

200 응답 상태:

| status | 필드 | Spring 처리 |
|---|---|---|
| validated | candidate, retrieved_chunks, validation_report, 모델/프롬프트/검증기/인덱스 버전 | 발행 제약 재확인 후 개인 퀴즈 저장 |
| insufficient_evidence | candidate=null, reason_codes | REJECTED, 공개 응답에 문항 없음 |
| validation_failed | candidate=null, reason_codes, validation_report | REJECTED, 실패 후보 비노출 |

candidate는 stem, options(4개, position/text), correct_option_position, explanation, concept_ids, evidence_chunk_ids를 가진다. 검증 규칙은 [생성 도메인](../domain/quiz-generation.md)을 따른다. JSON 파싱 성공이나 LLM의 `validated=true`만으로 발행하지 않는다. 실제 검증 단계·결과와 인용을 확인한다.

Spring에서 새로운 UUID와 소유자를 부여한다. Python이 생성한 quiz_id나 user_id로 서비스 DB에 쓰지 않는다. 내부 API 실패 시 생성 요청 상태를 FAILED로 기록하고 공개 오류 코드로 매핑한다.

C24 retrieved_chunks는 실제 검색 본문 evidence_text와 선택적 category/technology_version을 포함한다. Spring은 저장된 인용 snapshot만 공개하며 원문 업데이트와 독립적으로 보존한다.
