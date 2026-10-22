# 015 승인 출처 라이브 코퍼스와 Docker RAG 전환

Status: completed (2026-10-23)

## 목표·범위

- Gyoogle, 한국어 Wikipedia, RFC 9110, MDN HTTP, PostgreSQL 17의 이용 조건을 검토하고 승인 등록한다.
- 각 출처는 고정 revision/version, 제한된 URL·문서 수, 출처 표시를 유지한다.
- Docker에서 라이브 본문을 수집·정제·청킹하고 GMS 임베딩으로 별도 Chroma 인덱스를 만든다.
- 활성 인덱스를 사용하는 AI 서비스와 기존 퀴즈 → 오답 질문 경로를 검증한다.
- 영어 Wikipedia와 나머지 pending 출처는 범위 밖이며 활성화하지 않는다.

## 완료 조건

- [x] 5개 출처만 `approved`, `enabled`, `full-text`이고 검토 근거와 attribution이 등록된다.
- [x] 제한 수집 결과에 출처별 문서가 존재하고 normalized/chunk 무결성 검사가 통과한다.
- [x] 실제 수집 코퍼스의 GMS/Chroma 인덱스가 5개 이상 질의 평가 후 ACTIVE가 된다.
- [x] Docker AI가 fixture 대신 ACTIVE manifest를 읽고 Spring/퀴즈/채팅 E2E가 통과한다.
- [x] Python 회귀와 공통 검사를 실행하고 결과·잔여 위험을 이 문서에 기록한다.

## 검증·증거

API 키, Authorization, 쿠키와 원문 전체는 문서나 Git에 기록하지 않는다.

- 승인 출처: Gyoogle 고정 commit, 한국어 Wikipedia, RFC 9110, MDN HTTP 고정 commit,
  PostgreSQL 17. 영어 Wikipedia와 나머지 76개는 pending/disabled다.
- staging: `data/processed/ingestion-live-v3`, corpus digest
  `681995da3e11ad95c64bb98fc9d3a21fa15f82f5511bfde2554465db5d2d35a3`, 36문서
  (Gyoogle 10, Wikipedia 13, RFC 1, MDN 10, PostgreSQL 2), 794 staging 청크, 최종 실패 0.
- Wikipedia 리다이렉트를 canonical page ID/URL로 해석하고 퀴즈 개념 문서인 스레드(3214),
  포크(193595), 락(1929380)을 명시적으로 매핑했다.
- ACTIVE index: `csas-live-20261023-v4`, `text-embedding-3-small` 1,536차원,
  1,024 index 청크. `reports/rag-corpus-evaluation-v4.json`의 5/5 probe가 통과했다.
- E2E: `reports/rag-live-corpus-e2e-v4.json` PASS. Vue proxy → Spring Boot → Python RAG →
  ChromaDB/GMS 경로에서 오답 풀이 후 Wikipedia 스레드 문서를 인용한 답변을 확인했다. 외부 생성
  지연 변동을 수용하도록 내부 요청 timeout은 60초, E2E 클라이언트 timeout은 90초로 설정했다.
- 회귀: Python 57개 통과(라이브 Chroma 1개는 기본 실행에서 skip 후 별도 통과), Spring/PostgreSQL
  통합 테스트 35개와 Spotless·Checkstyle·bootJar 통과, Vue 단위 테스트 10개와 production build 통과.
  계획을 completed로 이동한 뒤 공통 문서 313개 링크와 하네스 19개도 통과했다.

## 잔여 위험

- activation probe는 5개뿐이며 C22의 15~20문항 정식 검색 평가를 대체하지 않는다.
- GitHub 익명 API 한도 소진 시 고정 commit 재수집은 reset 이후 재시도해야 한다. 이번 최종 코퍼스는
  앞서 성공한 MDN 10건을 보존한 staging에 Wikipedia 개념 문서 3건을 증분 추가했다.
- 삭제 문서 반영과 변경 문서만 재임베딩하는 C21 증분 인덱싱은 후속이다.
