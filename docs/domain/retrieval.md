# 검색 도메인

## C22 검색 품질 평가

`harness/evals/retrieval-v1.json`은 승인 코퍼스의 실제 문서 ID와 원문 URL을 사용한다. 운영체제,
네트워크, 데이터베이스, 자료구조·알고리즘, 소프트웨어·분산 시스템에서 각각 4문항을 관리한다.
정답 문서가 Top-K **청크 결과** 안에 나타나는지를 문서 단위 Hit Rate/Recall/MRR로 계산한다.
청크 정답 라벨이 없는 v1은 청크 지표를 0점으로 오인하지 않도록 `not_evaluated`로 기록한다.

평가 보고서는 데이터셋 버전, 코퍼스 digest, 임베딩 모델·차원, collection, 청킹 설정과 개별
검색 순위·거리·누락 근거를 함께 남긴다. Top-5 누락은 `relevant_document_not_in_top_k`로 분류해
임베딩 순위, 청킹, 메타데이터와 필터를 후속 점검할 수 있게 한다.

실행 명령은 `python scripts/rag_retrieval_eval.py --index-version <active-index>`이며 결과는 기본적으로
`reports/retrieval-evaluation.json`에 저장된다.

상태: 구조 청킹·임베딩 공급자·버전별 ChromaDB 적재/검색·manifest 활성화 gate를 구현했다. 승인 실코퍼스의 5개 activation probe와 퀴즈 문맥 E2E는 통과했으며, C22의 15~20문항 Top 5 평가는 후속이다.
입력은 검증된 CS 질문과 사용할 인덱스 버전, 선택적 concept_ids·서버가 확인한 문제 문맥이다.
질문 임베딩 → 벡터 검색 → 메타데이터 필터 → 제한된 청크 선택 → 검색 증거를 반환한다.

## 불변 조건
- 검색 문서와 질문은 같은 임베딩 모델·차원을 사용한다.
- 같은 인덱스 안에 다른 모델/차원을 섞지 않는다.
- 검색된 document_id·chunk_id·원문 메타데이터를 보존한다.
- 근거 선택은 품질 평가를 바탕으로 조정한다. 임의 유사도 숫자를 보편 기준처럼 사용하지 않는다.
- DB 실패·빈 결과·관련 근거 부족을 구분한다.
- 개념 필터로 우선 검색하고 부족하면 분야/전체로 확장한다. 질문에 매핑한 개념과 단순 검색 결과의 개념을 구분한다.
- 질문/생성에 같은 검색 인터페이스를 사용한다. Graph는 [2차 관계 모델](knowledge-graph.md)에 따른 별도 어댑터다.

평가: 실제 코퍼스와 연결한 20개 질문의 정답 근거가 Top 5에 포함되는 비율을 측정한다.
검색 성공은 답변 의미 정확성을 보장하지 않는다. [답변 도메인](answering.md)의 검증을 함께 수행한다.

2026-10-22 GMS/Chroma 라이브 연결 검증은 로컬 fixture 15청크로 수행했다. `text-embedding-3-large` 응답 차원은 3072였고 프로세스/스레드, TCP/UDP, 트랜잭션, 인덱스 질문은 관련 문서가 상위에 나타났다. 데드락 질문은 관련 문서가 fixture에 없어 무관한 결과만 반환했으므로 검색 품질 통과로 계산하지 않는다. 연결 성공과 실제 코퍼스 품질 평가는 구분한다.

2026-10-23 실코퍼스 `csas-live-20261023-v4`는 36문서/1,024 index 청크, `text-embedding-3-small` 1,536차원으로 구축했다. 출처군별 5개 probe가 모두 통과해 ACTIVE가 됐고, `concept:os-thread` 우선 검색으로 퀴즈 오답 질문이 한국어 Wikipedia 스레드 문서를 인용하는 E2E도 통과했다. 이 5개 probe는 C22의 정식 평가 데이터셋을 대체하지 않는다.

## 저장소 경계 (C02)

[ADR 0004](../decisions/0004-stack.md)에 따라 ChromaDB HttpClient를 providers 어댑터 뒤에 둔다. PostgreSQL은 개념 ID 원장이며 Python이 사용자·풀이 테이블을 수정하지 않는다. collection은 인덱스 버전별로 분리하고 ID는 chunk_id, document는 청크 본문, metadata는 source_id/document_id/revision/locator/url/index_version과 JSON 직렬화한 검수 개념 연결을 담는다. 파일 manifest는 모델·차원·청크 설정·코퍼스 digest와 collection을 연결하며 검증 결과가 있어야 ACTIVE로 전환한다.

manifest schema v2는 문서별 content hash와 chunk embedding key, indexed/last-seen 시각,
마지막 동기화 통계를 추가한다. manifest와 실제 Chroma 문서 청크 ID가 다르면 동일 문서도 복구
대상으로 분류한다. 부분 실패는 `last_run.failures`와 문서 `indexing_status`에 자격증명·응답 본문 없이
기록한다.
