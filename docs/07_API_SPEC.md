# 07. API SPEC — 공개·내부 API 명세 안내

기준은 [openapi.yaml](api/openapi.yaml) v0.5.0이다. C04의 익명 `GET /health`, C05~C07의 인증 API, C12~C13의 카테고리·READY 문제 조회·서버 채점/시도 저장, C17의 대화 생성·질문 API와 C23 대화 목록·상세·복원 API를 구현했다. 생성·me 학습 API는 설계 상태다. 표준 라이브러리로 참조를 확인할 수 있도록 YAML의 부분집합인 JSON 표기로 저장했다.

기존 `/api/v1/questions` 단독 초안은 대화 기반 API로 대체했다. 기존 동작 서비스는 없으므로 호환 endpoint를 추가하지 않는다. 모든 공개 경로는 `/api/v1`로 통일한다. Python API는 [내부 계약](api/internal-rag.md)으로 분리한다.

## 인증·접근

[ADR 0004](decisions/0004-stack.md)에 따라 Spring Security 쿠키 세션을 채택한다. Vue와 Spring을 동일 출처의 reverse proxy 뒤에 두고, 로그인 시 CSAS_SESSION 식별자를 회전한다. 쿠키는 HttpOnly·Secure·SameSite=Lax이며 브라우저 저장소에 토큰을 두지 않는다. 로컬 HTTP 예외는 개발 전용 설정에서 명시하고 운영 설정과 분리한다.

GET `/auth/csrf`는 인증 전에도 허용하며 토큰을 반환한다. 모든 POST는 가입/로그인도 포함해 X-CSRF-Token을 검증한다. 로그인·로그아웃 후 토큰을 다시 조회한다. 메모리 세션·유휴 30분/최대 12시간·BCrypt cost 12와 UTF-8 72바이트 상한을 채택한다. 비밀번호 문자 길이는 12~128자이며 두 상한을 함께 검증한다. 상세와 CORS·내부 API 보호는 [MVP 아키텍처](architecture.md)를 따른다.

가입/로그인/CSRF와 소개 화면만 익명 접근을 허용한다. 퀴즈·챗봇·생성·개념 탐색·모든 me API는 로그인 필수다. user_id를 본문에서 받아 소유자로 쓰지 않는다. 타인 개인 리소스는 404로 처리한다.

## 1차 경로

로그인 실패는 계정 없음/비밀번호 불일치 모두 401 INVALID_CREDENTIALS와 같은 메시지다. 계정이 없어도 동일 cost의 dummy BCrypt hash를 검증한다. 성공 시 사용자 ID만 담은 SecurityContext를 서버 세션에 저장하고 세션 ID와 CSRF 토큰을 회전한다. `/auth/me`는 세션의 본인 ID로 사용자 정보를 조회하며 요청 파라미터로 타인 ID를 받지 않는다. 익명·위조·만료 쿠키는 401이다. 세션 유휴 제한은 Tomcat 30분, 인증 시각 기준 절대 제한은 애플리케이션에서 12시간으로 집행한다. 재로그인은 새 인증 시각을 설정하며 서버 재시작 시 모든 메모리 세션을 잃는다.

로그아웃은 인증과 새 CSRF가 있는 POST만 허용하며 204를 반환한다. 서버 세션 무효화·SecurityContext 제거·CSAS_SESSION 쿠키 만료를 수행한다. 이전 쿠키 재사용과 중복 로그아웃은 401이다. 익명 학습 요청은 POST에 CSRF가 없어도 401이며 공개 가입/로그인의 CSRF 실패와 인증된 요청의 CSRF 실패는 403 CSRF_INVALID다. 역할 부족은 403 ACCESS_DENIED, 타인 개인 리소스는 404다. 오류의 request_id는 서버에서 발급하고 X-Request-Id 응답 헤더와 일치시킨다.

구현된 퀴즈 경로는 세션 사용자 범위에서 CURATED 또는 본인 소유 READY 문제만 조회한다. 답안 제출의 user_id는 세션에서만 얻고 선택지 소속과 문제 상태를 서버가 확인한다. 대화 POST는 본인 attempt와 quiz의 일치를 확인하고 DB에서 문제·선택지·채점 문맥을 복원한다. 모든 대화 GET도 조회 쿼리에서 user_id를 제한한다. Python에는 사용자 쿠키/식별정보를 전달하지 않으며 인용은 검색 결과 집합에서 다시 검증해 snapshot으로 저장한다.

아래 경로에 `/api/v1` 접두사를 붙인다.

| Method | 경로 | 동작 |
|---|---|---|
| GET | /auth/csrf | 상태 변경용 CSRF 토큰 |
| POST | /auth/signup | 가입, 자동 로그인하지 않음 |
| POST | /auth/login | 세션 생성/회전 |
| POST | /auth/logout | 세션 무효화·쿠키 만료 |
| GET | /auth/me | 현재 사용자 |
| GET | /quiz/categories | 접근 가능한 READY 문제의 분야별 수 |
| GET | /quizzes | 분야·난이도·개념 필터, 접근 가능한 READY 목록 |
| GET | /quizzes/{quiz_id} | 정답 없는 문제/선택지 |
| POST | /quizzes/{quiz_id}/attempts | 서버 채점·시도 저장·복습 갱신 |
| GET, POST | /chat/sessions | 본인 대화 목록·대화 생성 |
| GET | /chat/sessions/{session_id} | 본인 대화 상세 |
| GET, POST | /chat/sessions/{session_id}/messages | 대화 복원·RAG 질문 |
| POST | /quiz-generations | 관련 문제 1개 생성·검증·저장 |
| GET | /me/attempts | 본인 풀이 이력 |
| GET | /me/attempts/{attempt_id} | 본인 과거 버전 문제·선택·정오답·해설 |
| GET | /me/wrong-answers | 문제별 오답 복습 상태·최근 시도 ID |
| GET | /me/stats | 전체·분야별 정답률/시도 수 |

2차 경로 후보는 [graph-rag.md](api/graph-rag.md)에만 두며 현재 OpenAPI의 구현 대상에 포함하지 않는다.

## 문맥·정답·페이지

가입은 기존 `/api/v1/auth/signup`을 유지하며 `/register` 별칭은 제공하지 않는다. 이메일은 앞뒤 공백 제거 후 Locale.ROOT 소문자로 정규화한다. 공급자별 점/plus 별칭을 통합하지 않는다. Bean Validation과 DB UNIQUE가 중복을 막고 경합의 제약 위반도 409 EMAIL_ALREADY_EXISTS로 변환한다. 비밀번호는 trim하지 않으며 12~128자·UTF-8 72바이트 상한을 함께 적용한다. nickname은 생략/null 가능하며 입력 시 trim 후 1~40자다. 응답은 UUID id·email·nickname만 반환한다. 알 수 없는 입력 필드는 400으로 거부하고 엔티티/비밀번호/해시는 반환하지 않는다. 가입은 세션 로그인으로 취급하지 않는다.

일반 대화 생성은 `{title?}`, 문제 대화는 `{title?, quiz_id, attempt_id}`다. 두 ID가 같은 본인 풀이인지 확인하고 문제·선택·정오답·개념은 서버가 복원한다. 생성 이후 재풀이해도 대화의 원래 문맥은 바뀌지 않는다.

문제 응답 Quiz에는 정답·해설·is_correct·근거가 없다. AttemptResult에서만 이를 공개한다. 답안 제출은 정확히 한 트랜잭션에서 채점과 시도를 저장하고 저장 실패 시 500으로 롤백한다. AI 생성 문제도 같은 정책을 적용하고 개인 소유권을 검사한다. RETIRED 문제는 과거 결과로만 조회하며 새 제출은 409다.

대화 목록은 page/limit offset 페이지네이션을 사용하며 기본 20, 최대 50이다. 메시지는 기본·최대 50이고 DB `sequence_no` 오름차순으로 안정적으로 복원한다. 대화는 updated_at·ID 내림차순이며 빈 목록은 items=[], next_page=null이다. 다른 목록의 cursor 계약은 유지한다.

## 멱등성·생성·오류

답안 제출, 채팅 메시지와 생성은 Idempotency-Key(UUID)가 필수다. 작업 종류별 사용자 키 공간을 분리하며 같은 키·같은 정규화 입력은 같은 결과를 반환한다. 채팅은 세션별 키와 질문 hash를 저장하고 완료 응답을 재생한다. 같은 키로 다른 질문을 보내면 409, 처리 중이면 409 CHAT_IN_PROGRESS다. 실패 상태는 같은 키로 재시도하되 USER 메시지를 중복 저장하지 않는다.

생성은 ready/insufficient_evidence/validation_failed를 200으로 구분한다. ready에서만 quiz 객체가 있으며 나머지는 null이다. 후보 정답/해설/실패 문항은 공개하지 않는다. upstream 오류는 502, timeout은 504이며 생성 레코드가 있으면 FAILED로 기록한다. 같은 키는 저장된 실패를 반환하고 새 시도는 새 키를 쓴다.

Answer와 대화 메시지에는 등록 원장과 매핑한 concept_ids를 반환한다. 일반 챗봇에서 학습한 개념도 이 ID로 생성 요청에 연결한다. USER 메시지는 concept_ids=[], ASSISTANT는 확인된 ID만 포함한다. 매핑이 없으면 자동 생성 버튼을 비활성화하고 기존 분야/퀴즈의 개념을 선택하도록 안내한다.

메시지 전송은 동기 처리지만 외부 RAG 호출 동안 DB 트랜잭션을 열어 두지 않는다. USER와 pending ASSISTANT를 먼저 커밋하고 성공 시 답변·인용을 원자적으로 저장하며 실패 시 failed 상태를 별도 트랜잭션으로 기록한다. UI는 전송 중 버튼을 비활성화하고 새로고침 시 GET messages로 실제 저장 상태를 복원한다.

공통 오류는 request_id/code/message/timestamp(UTC ISO 8601)다. request_id가 추적 ID다. 400 입력 오류, 401 인증, 403 CSRF, 404 리소스 없음/타인 소유, 409 충돌, 429 제한, 500 내부 저장 실패, 502 upstream, 504 deadline이다. 422 의미 입력 처리 불가와 503 일시적 가용성 장애는 [공통 규칙](architecture.md)의 예약 상태이며 현재 경로 반환 상태는 유지한다. 근거 부족은 정상 도메인 상태이며 시스템 오류를 감추는 용도가 아니다.

## 계약 변경·검사

OpenAPI → 요청/응답 예시·계약 검사 → Java DTO·Python 매핑·Vue 타입 순서로 함께 갱신한다. 수동 작성 타입의 중복은 줄이고 실제 생성 도구는 버전 고정 후 결정한다. 숫자/길이 제한은 제안 기본값이며 변경 시 계약·검사도 갱신한다.

스키마로 표현하기 어려운 문맥 ID 일치·정답 비노출·상태별 null·소유권·멱등성은 계약 테스트로 검증한다. [testing](09_TEST_SCENARIO.md)과 [하네스 연계](harness-workflow.md)를 따른다.
