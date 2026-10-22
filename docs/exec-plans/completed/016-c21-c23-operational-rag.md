# 016 C21~C23 운영형 RAG와 사용자 대화 복원

Status: completed

## 목표

- C21: content hash·인덱스 설정·문서별 청크 manifest를 기준으로 신규/수정/동일/삭제를 판별하고,
  변경 청크만 임베딩하는 안전한 증분 인덱싱을 구현한다.
- C22: 현재 승인 코퍼스의 실제 document/chunk ID를 사용한 20문항 검색 평가셋과
  Hit Rate@1/3/5, Recall@1/3/5, MRR, 누락 근거 보고서를 구현한다.
- C23: 기존 V6 대화 저장을 확장해 일반/퀴즈 대화 목록·상세·메시지 복원, 멱등 요청,
  실패 상태와 사용자 소유권 격리를 Spring/PostgreSQL/Vue에서 완성한다.

## 완료 조건

- [x] C21 단위·실제 Chroma 통합 검사 후 `feat(ingest): implement incremental indexing` 커밋
- [x] C22 20문항 데이터셋·평가 실행·테스트 후 `test(rag): add a retrieval evaluation dataset` 커밋
- [x] C23 DB/API/UI·두 사용자 통합 검사 후 `feat(chat): persist user conversations` 커밋
- [x] Python, Spring/PostgreSQL, Vue, 공통 검사와 Docker E2E 증거 기록
- [x] 완료 후 이 계획을 completed로 이동하고 current-task를 갱신

## 안전 경계

- 삭제는 명시적으로 완전 수집이 확인된 source에만 적용한다.
- 임베딩/Chroma 실패 전에는 기존 문서 청크를 제거하지 않는다.
- `.env`, 공급자 키, 쿠키, 원문 전체와 생성 data/reports는 커밋하지 않는다.
- Python은 사용자 DB를 수정하지 않고 Spring만 인증·소유권·대화 저장을 담당한다.

## 검증 증거

- C21 단위 11개와 실제 Chroma 통합 2개 통과.
- ACTIVE v4 dry-run: 전체 36, 신규 0, 수정 0, 동일/skip 36, 삭제·임베딩·실패 0.
- C21 커밋: `ffac332 feat(ingest): implement incremental indexing`.
- 요구 모델로 v5를 새로 구축하고 activation probe 5/5 통과: 36문서, 1,024청크,
  `text-embedding-3-large` 3,072차원. 이어진 증분 실행은 36문서 skip, 임베딩·실패 0건이다.
- C22 단위 5개 통과. v5 실제 20문항 평가는 Hit/Recall@1 0.90, @3 0.90, @5 0.95,
  MRR 0.9125다. `network-04` 조건부 요청 문서가 Top-5에서 누락됐고 청크 라벨은 아직 없다.
- C22 커밋: `7bbff7f test(rag): add a retrieval evaluation dataset`.
- C23 Spring 전체 통합 검사 39개, Vue 단위 11개·빌드·lint·typecheck와 Playwright 대화 복원 검사를 통과했다.
- Docker 전체 스택에서 V7 migration, 사용자 격리, 멱등 재생·충돌, RAG 실패 저장·재시도와 새로고침 후 대화·인용 복원을 확인했다.
- 실제 Vue proxy → Spring → Python → Chroma/GMS E2E와 Playwright 8개가 통과했고 환경 변수 기반 live-auth 1개만 조건부 skip됐다.
- 공통 문서·bootstrap·harness 검사는 문서 링크 315개와 harness 단위 19개를 포함해 통과했다.
