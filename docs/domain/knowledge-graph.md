# CS 지식 관계와 Graph RAG 확장

상태: 2차 설계 제안. Neo4j는 후보이며 버전·운영 방식은 도입 ADR에서 확정한다. 1차 실행 의존성에 Graph DB를 넣지 않는다.

## 개념과 관계

노드: `Concept {concept_id, canonical_name, domain, aliases}`. ID 원장은 PostgreSQL concepts다. 원문에서 추출한 명칭은 별칭/문맥을 검토하고 매핑한다. 이름이 같은 별개 개념을 자동 병합하지 않는다.

| 관계 | 방향·의미 | 검증 원칙 |
|---|---|---|
| CAN_USE | A가 B를 활용할 수 있음 | 필수 의존성을 뜻하지 않음 |
| ADDRESSES_RISK_WITH | A의 특정 위험을 B로 완화 | risk와 적용 조건 설명 필수 |
| PREREQUISITE_OF | A가 B 학습의 선행 개념 | 학습상 필요와 기술상 필수 구분, 순환 검토 |
| IS_A | A가 B의 하위 유형 | 단순 유사성과 구분 |
| PART_OF | A가 B의 구성 요소 | 사용 관계와 구분 |
| ALTERNATIVE_TO | 특정 조건에서 대안 관계 | 대체 가능한 조건 명시, 표시 시 양방향 해석 |

```cypher
(MSA)-[:CAN_USE]->(Kubernetes)
(MSA)-[:CAN_USE]->(EventDrivenArchitecture)
(MSA)-[:ADDRESSES_RISK_WITH]->(CircuitBreaker)
(MSA)-[:CAN_USE]->(SagaPattern)
```

위 표기는 요구사항의 의미 예시이며 수집·검증된 데이터가 아니다. MSA→Kubernetes를 `REQUIRES`로 바꾸지 않는다. `REQUIRES`는 초기 허용 관계 목록에서 제외한다.

## 근거와 버전

관계는 `relation_id, from_concept_id, to_concept_id, type, description, scope, evidence_refs[], review_status, extractor_version, graph_version`을 가진다. evidence_refs에는 source_id/document_id/revision/chunk_id/locator가 필요하다. 상태는 CANDIDATE/VERIFIED/REJECTED다. VERIFIED만 사용자 지도와 답변에 사용한다.

동일 개념쌍이라도 관계 타입·적용 조건이 다르면 별도 관계다. 문서에 단어가 함께 나오거나 링크가 있다는 이유만으로 관계를 확정하지 않는다. 원문이 바뀌면 영향을 받는 관계를 재검증하고, 기존 그래프 버전은 재현 가능하게 유지한다.

## 구축·조회·복구

1. 1차 개념 원장과 승인된 원문 리비전으로 제한된 분야의 그래프 후보를 만든다.
2. 동의어·관계 의미·방향·근거를 검토하고 버전 있는 그래프를 발행한다.
3. 질의의 concept_id에서 허용 타입·최대 2홉·노드/관계 수 상한으로 탐색한다.
4. 관계가 가리킨 원문 청크를 다시 확인하고 Vector 근거와 결합한다. 그래프 연결만으로 사실을 생성하지 않는다.
5. Graph 장애 시 Vector 답변으로 강등하고 관계 탐색 실패 상태를 표시한다. Graph가 없는 상태도 1차 서비스는 정상 동작한다.

Graph는 원문·개념 원장·관계 manifest에서 재구축 가능한 투영이다. 온라인 서비스 요청이 PostgreSQL과 Graph를 동시에 쓰도록 만들지 않는다. 초기에는 재실행 가능한 배치 동기화와 누락 ID 검사를 사용하고, 필요 시 outbox를 별도 설계한다.

## 학습 기록 연결

시도 → quiz_concepts → concepts → Graph concept_id로 연결한다. 취약도는 우선 개념별 오답/시도 수로 설명 가능하게 표시하고, 적은 표본을 숙련도 진단처럼 단정하지 않는다. 선행 개념·관련 개념 추천은 Graph 품질 검증 후 별도 작업으로 구현한다.

검증: 위 MSA 관계 의미, 미검증 관계 비노출, 방향·중복·별칭 충돌, 근거 삭제/개정, 최대 홉/노드 제한, 타 사용자 이력 격리, Vector 대비 관계 질문 평가를 포함한다.
