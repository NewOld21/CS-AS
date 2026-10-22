# 014 GMS API·RAG 라이브 검증

## 목표와 경계

`backend/.env`를 Compose AI 서비스에 주입해 GMS Chat/Embedding, ChromaDB, Spring Boot, Vue 퀴즈 AS 경로를 실제 검증한다. 비밀값은 코드·Git·로그에 남기지 않는다. 기존 DB·컬렉션은 삭제하지 않으며 pending 출처를 승인하지 않는다.

## 구현

- GMS/OpenAI 호환 환경변수와 429·5xx·timeout 제한 재시도, 인증 실패 비재시도를 provider에 추가했다.
- Docker 전체 개발 스택과 GMS 기반 로컬 검증 컬렉션, health check를 구성했다.
- `rag_diagnostics.py`와 `rag_e2e.py`로 라이브/회귀 검사를 분리했다.
- GMS JSON 답변 형식과 검색 결과에 포함된 Citation ID만 허용하는 계약을 강화했다.

## 2026-10-22 검증 증거

- GMS Embedding: PASS, `text-embedding-3-large`, 실제 3072차원.
- GMS Chat: PASS, `gpt-5-mini`, 한국어 JSON 답변.
- ChromaDB: 기존 `csas-local-dev-v1`(64차원, 15청크)을 보존하고 별도 `csas-gms-live-dev-v1`(3072차원, 15청크)을 생성했으며 재기동 후 count가 유지됐다.
- Citation: PASS, 검색된 `POSIX threads`·`fork` 청크 2개만 인용.
- 근거 부족: PASS, 존재하지 않는 concept 필터에서 `insufficient_evidence`.
- 전체 E2E: PASS, Vue proxy→Spring→Python→Chroma/GMS, 오답 제출 후 “왜 틀렸어?”와 HTTPS 출처 반환.
- Python: 54 tests PASS, 실제 Chroma integration 포함.
- Spring/PostgreSQL: 35 tests PASS, Spotless·Checkstyle·bootJar PASS.
- Vue: 10 tests PASS, build PASS, production dependency audit 0 vulnerabilities.
- 실제 수집: 등록부 81개, approved/enabled 0개, normalized documents 0, chunks 0. 정책상 SKIP.

비밀 없는 상세 결과는 Git 제외 경로 `reports/rag-live-diagnostics.json`, `reports/rag-live-e2e.json`에 저장한다.

## 미해결

- gyoogle/Wikipedia/공식 문서는 이용 조건 승인 전이라 라이브 수집하지 않았다.
- 데드락 질문은 15개 fixture에 관련 문서가 없어 검색 결과 관련성이 부족했다.
- 실제 코퍼스 20문항 Top 5 평가와 운영 ACTIVE 인덱스 전환은 후속이다.
