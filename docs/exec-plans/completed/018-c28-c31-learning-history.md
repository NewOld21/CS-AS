# 018 C28~C31 학습 이력·복습·마이페이지

Status: complete

## 범위와 완료 조건

- 수정 범위: backend/src/, frontend/, docs/. 기존 quiz_attempts·서버 채점·인증·생성/근거 패널을 재사용한다.
- C28: 소유자 한정 이력/상세, 시간+ID 커서·필터·전체 개수, 과거 문제·근거 snapshot 보존.
- C29: NEEDS_REVIEW/RESOLVED 상태·오답 목록·기존 attempts API의 retry_of_attempt_id, 시도와 상태의 원자성·통계.
- C30: /me 마이페이지·오답노트·과거 결과·재풀이, 로딩/빈 값/장애·모바일/키보드.
- C31: 생성 문제→오답→이력→재풀이→해결·재로그인 복원·타인 접근 차단 E2E.
- 단계마다 검사·문서·지정 커밋을 수행한다. 실제 모델/검색과 mock 검증은 구분한다.

## 시작 상태

2026-10-23: 386a73f 기반, 작업 트리 깨끗함. Docker 검사 이미지·전용 PostgreSQL Compose·Vue 도구 사용 가능. 루트/AI .env와 ACTIVE 데이터는 없다. 요청은 C29 목록 요구 중간에서 끊겼으며 이후 세부사항은 기존 PRD/ERD/API를 적용한다.

## 증거와 인계

각 단계의 실제 검사·커밋·미실행 항목을 추가한다.

### C28

전용 PostgreSQL에서 HistoryIntegrationTest 4개와 GenerationIntegrationTest 6개 통과. 빈 이력/401·사용자 격리·필터/상한·동률 커서/사용자 및 필터 바인딩·과거 문제 수정/retire 이후 snapshot 복원과 AI 생성 문제의 동일 이력 조회를 확인했다. 명령: Docker checks의 `gradle --no-daemon spotlessApply test --tests com.csas.HistoryIntegrationTest --tests com.csas.GenerationIntegrationTest`.

### C29

Docker 전용 PostgreSQL의 ReviewIntegrationTest 5개·QuizAttemptIntegrationTest 5개·HistoryIntegrationTest 4개 통과. 오답→정답→오답 재개, 중복 키 재생의 상태 불변, 최초 정답 미등록, 0건 accuracy=null, 분야·출처·상태/커서/사용자 격리, 잘못된 retry 참조, retired 차단, 복습 쓰기 실패의 시도 롤백과 기존 동시 제출을 검사했다. 별도 재채점 테이블/로직 없이 기존 attempts POST를 사용한다.

### C30

Vue 타입 검사·production build 및 Vitest 17개 통과. Chrome history.spec.ts 3개 통과: 실제 화면의 서버 커서/필터 초기화·390px overflow 없음, 오답노트→답 비노출 재풀이·응답 유실 후 reload와 동일 키 재확인, 빈 이력/통계 503·retired 당시 해설·401 로그인 이동. 브라우저 API는 fixture이며 DB 영속성은 C31의 실제 Spring HTTP/PostgreSQL 검사로 구분한다. 사용자 추가 응답의 재로그인 기록 보존·학습 루프 요구를 C31에 반영한다.

### C31

2026-10-23 KST 검증:

- 전용 Docker PostgreSQL과 실제 Spring HTTP: `docker compose -f compose.backend-test.yaml run --rm checks gradle --no-daemon spotlessApply check bootJar`, 55개 테스트 통과, 실패/skip 0. 새 생성 학습 루프 테스트는 질문→본인 대화 개념 기반 생성→오답→오답노트→새 키 재풀이→중복 키 replay→해결→로그아웃/401→재로그인 후 동일 이력·당시 오답·정답률 50%와 타인 접근 404를 확인했다. RAG gateway만 Mockito 대역이다.
- 최초 전체 검사에서 기존 AuthorizationIntegrationTest의 미구현 이력 API 404 기대가 실패했다. 실제 구현 이후 빈 목록/total_count=0의 200 계약으로 수정한 뒤 전체 55개를 다시 통과했다.
- Chrome `ui.spec.ts history.spec.ts` 11개 통과. 생성 AI 문제를 오답 제출하고 오답노트에서 정답 없이 다시 풀어 해결·과거 오답 보존·통계를 확인한다. 브라우저 API는 fixture이며 GMS·Chroma 실호출을 뜻하지 않는다. 페이지/필터·모바일·WCAG AA 자동 검사와 응답 유실/reload/동일 키도 검증한다.
- Vue lint/format/typecheck/build, Vitest 17개 통과. 재풀이 문맥에서 새로 생성한 다른 문제에 이전 retry ID를 전달하지 않도록 제한하고 일반 풀이에도 동일 키 복원을 적용했다.
- 비밀/빌드 산출물을 제외한 candidate snapshot의 Python Docker 회귀 78개 중 76개 통과, 실제 Chroma 연결 2개 skip. mock 모델·검색과 실제 Python 내부 HTTP/독립 검증 회귀를 포함한다.
- 같은 Linux snapshot의 `python3 scripts/verify.py`: 문서 링크·bootstrap 설정·하네스 19개 통과. 공통 bootstrap 통과는 플랫폼 full-profile 완료를 뜻하지 않는다.

커밋: C28 b0b93ca, C29 dbcd242, C30 d107e80, C31은 이 계획과 함께 기록한다. 공개 API는 기존 /me 경로와 NEEDS_REVIEW/RESOLVED 상태를 유지한다. V10/V11은 기존 데이터에서 snapshot/복습 상태를 backfill하며 운영 적용 전 별도 백업·migration 검토가 필요하다. 이번 작업에서 개발/운영 DB는 변경하지 않았다.

남은 외부 검증: 현재 .env/GMS 키와 ACTIVE corpus가 없어 실제 GMS·승인 코퍼스/Chroma를 통과했다고 주장하지 않는다. 기존 017의 모델 생성 표본/사람 검수·실서비스 RAG 검증은 그대로 후속이다. 기록 DB 재시작 후 영속성은 PostgreSQL 저장 구조에 의존하며 이번에는 로그아웃/재로그인 복원만 실행했다.
