# Graph API 확장 예약

상태: 2차 제안. 현재 [OpenAPI](openapi.yaml)의 1차 구현 대상에 포함하지 않는다. [Graph 모델](../domain/knowledge-graph.md)의 품질 검증 후 별도 계약을 추가한다.

| API 후보 | 의미 |
|---|---|
| GET /api/v1/concepts?query= | 개념·별칭 검색 |
| GET /api/v1/concepts/{concept_id}/relations?hops=1 | 허용 관계와 근거를 가진 제한 탐색 |

관계 응답은 graph_version, nodes(concept_id/name), edges(relation_id/from/to/type/description/scope/evidence_refs)를 가진다. 미검증 관계는 제외한다. 홉 수는 1~2로 제한하고 노드·간선 상한·cursor·timeout을 명세한다. 출처가 사라졌거나 그래프가 갱신 중이면 상태를 구분한다.

관계 기반 퀴즈는 신규 채점 경로를 만들지 않고 기존 생성 요청에 relation_ids와 graph_version을 추가하는 방향을 검토한다. 권한은 기존 로그인 정책을 유지하며, 사용자별 추천 이력은 타인에게 노출하지 않는다.
