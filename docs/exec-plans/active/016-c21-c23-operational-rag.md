# 016 C21~C23 운영형 RAG와 사용자 대화 복원

Status: in-progress

## 목표

- C21: content hash·인덱스 설정·문서별 청크 manifest를 기준으로 신규/수정/동일/삭제를 판별하고,
  변경 청크만 임베딩하는 안전한 증분 인덱싱을 구현한다.
- C22: 현재 승인 코퍼스의 실제 document/chunk ID를 사용한 20문항 검색 평가셋과
  Hit Rate@1/3/5, Recall@1/3/5, MRR, 누락 근거 보고서를 구현한다.
- C23: 기존 V6 대화 저장을 확장해 일반/퀴즈 대화 목록·상세·메시지 복원, 멱등 요청,
  실패 상태와 사용자 소유권 격리를 Spring/PostgreSQL/Vue에서 완성한다.

## 완료 조건

- [x] C21 단위·실제 Chroma 통합 검사 후 `feat(ingest): implement incremental indexing` 커밋
- [ ] C22 20문항 데이터셋·평가 실행·테스트 후 `test(rag): add a retrieval evaluation dataset` 커밋
- [ ] C23 DB/API/UI·두 사용자 통합 검사 후 `feat(chat): persist user conversations` 커밋
- [ ] Python, Spring/PostgreSQL, Vue, 공통 검사와 Docker E2E 증거 기록
- [ ] 완료 후 이 계획을 completed로 이동하고 current-task를 갱신

## 안전 경계

- 삭제는 명시적으로 완전 수집이 확인된 source에만 적용한다.
- 임베딩/Chroma 실패 전에는 기존 문서 청크를 제거하지 않는다.
- `.env`, 공급자 키, 쿠키, 원문 전체와 생성 data/reports는 커밋하지 않는다.
- Python은 사용자 DB를 수정하지 않고 Spring만 인증·소유권·대화 저장을 담당한다.

## 검증 증거

- C21 단위 11개와 실제 Chroma 통합 2개 통과.
- ACTIVE v4 dry-run: 전체 36, 신규 0, 수정 0, 동일/skip 36, 삭제·임베딩·실패 0.
- 커밋 해시는 커밋 생성 후 기록한다.
