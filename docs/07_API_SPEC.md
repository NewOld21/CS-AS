# 07. API SPEC — 공개·내부 API 명세 안내

기준은 [openapi.yaml](api/openapi.yaml) v0.4.0이다. C04의 익명 `GET /health`는 DB readiness를 반환한다(UP=200, DOWN=503, 상세 비노출). 인증 API는 C05~C07에서 순차 구현하며 학습 API는 설계 상태다. 표준 라이브러리로 참조를 확인할 수 있도록 YAML의 부분집합인 JSON 표기로 저장했다.

기존 `/api/v1/questions` 단독 초안은 대화 기반 API로 대체했다. 기존 동작 서비스는 없으므로 호환 endpoint를 추가하지 않는다. 모든 공개 경로는 `/api/v1`로 통일한다. Python API는 [내부 계약](api/internal-rag.md)으로 분리한다.

## 인증·접근

[ADR 0004](decisions/0004-stack.md)에 따라 Spring Security 쿠키 세션을 채택한다. Vue와 Spring을 동일 출처의 reverse proxy 뒤에 두고, 로그인 시 CSAS_SESSION 식별자를 회전한다. 쿠키는 HttpOnly·Secure·SameSite=Lax이며 브라우저 저장소에 토큰을 두지 않는다. 로컬 HTTP 예외는 개발 전용 설정에서 명시하고 운영 설정과 분리한다.

GET `/auth/csrf`는 인증 전에도 허용하며 토큰을 반환한다. 모든 POST는 가입/로그인도 포함해 X-CSRF-Token을 검증한다. 로그인·로그아웃 후 토큰을 다시 조회한다. 메모리 세션·유휴 30분/최대 12시간·BCrypt cost 12와 UTF-8 72바이트 상한을 채택한다. 비밀번호 문자 길이는 12~128자이며 두 상한을 함께 검증한다. 상세와 CORS·내부 API 보호는 [MVP 아키텍처](architecture.md)를 따른다.

가입/로그인/CSRF와 소개 화면만 익명 접근을 허용한다. 퀴즈·챗봇·생성·개념 탐색·모든 me API는 로그인 필수다. user_id를 본문에서 받아 소유자로 쓰지 않는다. 타인 개인 리소스는 404로 처리한다.

## 1차 경로

아래 경로에 `/api/v1` 접두사를 붙인다.

| Method | 경로 | 동작 |
|---|---|---|
| GET | /auth/csrf | 상태 변경용 CSRF 토큰 |
| POST | /auth/signup | 가입, 자동 로그인하지 않음 |
| POST | /auth/login | 세션 생성/회전 |
| POST | /auth/logout | 세션 무효화·쿠키 만료 |
| GET | /auth/me | 현재 사용자 |
| GET | /quizzes | 분야·난이도·개념 필터, 접근 가능한 READY 목록 |
| GET | /quizzes/{quiz_id} | 정답 없는 문제/선택지 |
| POST | /quizzes/{quiz_id}/attempts | 서버 채점·시도 저장·복습 갱신 |
| GET, POST | /chat/sessions | 본인 대화 목록·대화 생성 |
| GET, POST | /chat/sessions/{session_id}/messages | 대화 복원·RAG 질문 |
| POST | /quiz-generations | 관련 문제 1개 생성·검증·저장 |
| GET | /me/attempts | 본인 풀이 이력 |
| GET | /me/attempts/{attempt_id} | 본인 과거 버전 문제·선택·정오답·해설 |
| GET | /me/wrong-answers | 문제별 오답 복습 상태·최근 시도 ID |
| GET | /me/stats | 전체·분야별 정답률/시도 수 |

2차 경로 후보는 [graph-rag.md](api/graph-rag.md)에만 두며 현재 OpenAPI의 구현 대상에 포함하지 않는다.

## 문맥·정답·페이지

일반 대화 생성은 `{}`, 문제 대화는 `{quiz_id, attempt_id}`다. 두 ID가 같은 본인 풀이인지 확인하고 문제·선택·정오답·개념은 서버가 복원한다. 생성 이후 재풀이해도 대화의 원래 문맥은 바뀌지 않는다.

문제 응답 Quiz에는 정답·해설·is_correct·근거가 없다. AttemptResult에서만 이를 공개한다. AI 생성 문제도 같은 정책을 적용하고 개인 소유권을 검사한다. RETIRED 문제는 과거 결과로만 조회하며 새 제출은 409다.

페이지 기본 limit=20, 최대 100이다. cursor는 불투명 문자열이고 필터/정렬 범위에 묶는다. 문제는 ID 오름차순, 대화/시도는 생성 시각·ID 내림차순, 메시지는 시간·ID 오름차순, 오답은 최신 시도 시각·ID 내림차순으로 제안한다. 빈 목록은 items=[], next_cursor=null이다.

## 멱등성·생성·오류

답안 제출과 생성은 Idempotency-Key(UUID)가 필수다. 작업 종류별 사용자 키 공간을 분리하며 같은 키·같은 정규화 입력은 같은 결과를 반환한다. 제출의 request_hash에는 경로의 quiz_id도 포함한다. 같은 작업 종류에서 다른 본문/대상에 같은 키를 쓰면 409다. 생성 처리 중 중복은 409 GENERATION_IN_PROGRESS, 이후 같은 키로 결과를 복원한다.

생성은 ready/insufficient_evidence/validation_failed를 200으로 구분한다. ready에서만 quiz 객체가 있으며 나머지는 null이다. 후보 정답/해설/실패 문항은 공개하지 않는다. upstream 오류는 502, timeout은 504이며 생성 레코드가 있으면 FAILED로 기록한다. 같은 키는 저장된 실패를 반환하고 새 시도는 새 키를 쓴다.

Answer와 대화 메시지에는 등록 원장과 매핑한 concept_ids를 반환한다. 일반 챗봇에서 학습한 개념도 이 ID로 생성 요청에 연결한다. USER 메시지는 concept_ids=[], ASSISTANT는 확인된 ID만 포함한다. 매핑이 없으면 자동 생성 버튼을 비활성화하고 기존 분야/퀴즈의 개념을 선택하도록 안내한다.

메시지 전송은 동기 처리다. 세션별 동시 전송을 직렬화하고, UI는 전송 중 버튼을 비활성화하며 자동 재전송하지 않는다. 응답이 유실되면 GET messages로 저장 여부를 먼저 확인한다. 본인 요청의 저장 실패는 500이며 저장 성공으로 표시하지 않는다.

공통 오류는 request_id/code/message/timestamp(UTC ISO 8601)다. request_id가 추적 ID다. 400 입력 오류, 401 인증, 403 CSRF, 404 리소스 없음/타인 소유, 409 충돌, 429 제한, 500 내부 저장 실패, 502 upstream, 504 deadline이다. 422 의미 입력 처리 불가와 503 일시적 가용성 장애는 [공통 규칙](architecture.md)의 예약 상태이며 현재 경로 반환 상태는 유지한다. 근거 부족은 정상 도메인 상태이며 시스템 오류를 감추는 용도가 아니다.

## 계약 변경·검사

OpenAPI → 요청/응답 예시·계약 검사 → Java DTO·Python 매핑·Vue 타입 순서로 함께 갱신한다. 수동 작성 타입의 중복은 줄이고 실제 생성 도구는 버전 고정 후 결정한다. 숫자/길이 제한은 제안 기본값이며 변경 시 계약·검사도 갱신한다.

스키마로 표현하기 어려운 문맥 ID 일치·정답 비노출·상태별 null·소유권·멱등성은 계약 테스트로 검증한다. [testing](09_TEST_SCENARIO.md)과 [하네스 연계](harness-workflow.md)를 따른다.
