# 018 C28~C31 학습 이력·복습·마이페이지

Status: active

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
