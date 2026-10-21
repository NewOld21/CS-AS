# 006 지식 관계 지도·Graph RAG

Status: planned

## 목표·범위
- FR-11/12: 개념 간 의미 있는 관계를 탐색하고 문서 근거와 함께 설명한다.
- 선행: [005](005-complete-learning-loop.md)의 학습 루프 전체 검증, 공통 개념 원장과 문서 리비전.
- 수정 경로: backend/, frontend/, docs/. Graph 검사 등록은 별도 하네스 변경 단위다.
- 제외: 학습 이력 기반 자동 추천 모델·무제한 그래프 탐색·자동 미검증 관계 발행.

## 완료 조건
- [ ] Neo4j 등 저장소·버전·운영 조건·대안 비교 ADR 채택.
- [ ] 개념 별칭·관계 의미/방향·근거·검증 상태·graph_version 정의.
- [ ] VERIFIED 관계만 발행, 원장/원문에서 재구축 가능한 배치 검증.
- [ ] 최대 2홉·크기 상한·timeout·Graph 장애 시 Vector 강등.
- [ ] 관계 지도에서 노드·간선 설명·근거 표시.
- [ ] 관계 API와 내부 검색 계약·회귀 검사 확장.
- [ ] MSA→Kubernetes는 CAN_USE이며 필수 관계가 아님을 확인.
- [ ] Vector 단독 대비 고정 관계 질문의 검색/설명 품질과 1차 기능 회귀 평가.

## 검증·인계
설계: [knowledge-graph](../../domain/knowledge-graph.md), [API 예약](../../api/graph-rag.md). 현재 미실행이다. 실제 graph_version·원문/개념 매핑·검증 증거와 미해결 관계를 기록한다. 추천 확장은 별도 계획으로 작성한다.
