# 004 인증·퀴즈·학습 기록·Vector RAG

Status: in progress — C09~C17 quiz, Vector RAG and contextual chat path implemented

## 목표·범위
- FR-01~07: 로그인한 사용자가 퀴즈를 풀고 결과를 보존하며, 그 문맥으로 AS에게 질문한다.
- 수정 경로: backend/, frontend/, docs/. harness/의 task·검사 등록은 별도 검토 가능한 변경 단위로 구분한다.
- 제외: AI 퀴즈 생성, 마이페이지/오답 상세 UI(005), Graph RAG, 운영 배포.
- 선행: [002 bootstrap](002-service-bootstrap.md)의 버전·빌드·검사·계약 기반.

## 구현 순서
1. ERD migrations·개념 seed·검수 문제 seed·전용 테스트 DB.
2. 가입·로그인·세션/CSRF·소유권과 문제 조회/서버 채점.
3. 시도 멱등성·재풀이·복습 상태를 원자적으로 저장.
4. 승인 출처의 제한 코퍼스·개념 연결·ChromaDB 적재·실제 검색 평가.
5. 대화 생성·복원·문제 문맥 질문·출처·근거 부족/장애 처리.

## 완료 조건
- [x] 익명 학습 호출 거부, 비밀번호/세션 보호·로그아웃 확인.
- [x] 문제 조회에 정답/해설 비노출, 다른 문제 선택지 거부.
- [ ] 재전송/동시 요청 중복 없음, 새 키의 시도 누적, 복습 원자 갱신.
- [ ] 문맥 질문에 문제·본인 선택·정오답·개념 적용, 타인 리소스 거부.
- [ ] 재로그인 후 본인 시도·대화 복원.
- [ ] 인용·검색·근거 부족·공격 문서·timeout 평가와 대표 답변 사람 검토.
- [ ] 기계 판독 task/검사 등록·문서 갱신·검증 증거 확보.

## 검증·인계
기준: [testing](../../09_TEST_SCENARIO.md), 계약: [OpenAPI](../../api/openapi.yaml), 설계: [learning](../../domain/learning.md).
C09~C13 증거(2026-10-22): PostgreSQL 17.9 전용 tmpfs DB에서 인증 17개, 스키마 3개, 시드 3개, 조회 4개, 채점/멱등성 5개 통합 테스트를 통과했다. Checkstyle main/test도 통과했다. 전체 `check bootJar`는 기존 CRLF 파일에 대한 Spotless 위반 때문에 테스트 전에 중단되어 최종 인계에 구분 기록한다. review_states·대화/RAG·하네스 등록은 아직 미구현이므로 이 계획은 active에 유지한다. 다음은 이 계획의 남은 범위이며, 이후 [005](005-complete-learning-loop.md)로 진행한다.

C14~C17 증거(2026-10-22): [013 완료 계획](../completed/013-c14-c17-vector-learning-loop.md)의 수집 JSONL·Chroma 인덱스·내부 답변·풀이 문맥 대화 경로와 검증 결과를 따른다. 대화 생성/질문 POST는 구현했으나 대화 GET 복원, review_states·통계·실코퍼스 평가는 남아 있어 이 계획은 active다.
