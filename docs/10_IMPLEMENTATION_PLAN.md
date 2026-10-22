# 10. IMPLEMENTATION PLAN — 단계별 구현 계획

사용자 확정: 22시간 제한 없이 학습 루프 전체를 1차 개발 목표로 한다. C14~C17에서 3단계의 코드 경로와 fixture 통합을 구현했지만 승인 코퍼스·외부 모델 실평가 전에는 1차 RAG 운영 완료로 판정하지 않는다. 단계별 결과를 검증하고 FR-01~10 전체가 통과했을 때 1차 완료로 판정한다.

| 순서 | 범위 | 산출물·완료 기준 |
|---|---|---|
| 1. 환경·계약·서비스 골격 | 1차 기반 | [002](exec-plans/active/002-service-bootstrap.md): 버전·lockfile·health·세션/CSRF 기반·DTO·검사 등록 |
| 2. 인증·퀴즈·학습 원장 | 1차 기본 | [004](exec-plans/active/004-core-learning.md): 가입→로그인→퀴즈→채점→기록·오답 상태 |
| 3. 코퍼스·Vector RAG·문맥 질문 | 1차 기본 | 004: 승인 출처·개념 매핑·멱등 적재·인덱스·대화·출처·근거 부족 |
| 4. 관련 문제·복습 UI | 1차 완성 | [005](exec-plans/active/005-complete-learning-loop.md): AI 생성/검증·개인 문제·마이페이지·재풀이 |
| 5. 평가·오류 복구·출시 판정 | 1차 완료 | 계약·통합·E2E·RAG/생성 평가·사람 검토·인계 기록 |
| 6. 관계 지도·Graph RAG | 2차 확장 | [006](exec-plans/active/006-graph-rag.md): 관계 의미·근거·그래프·통합 검색 |
| 7. 취약 개념 연결 학습 | 후속 | 실제 학습 이력과 검증된 관계를 활용한 설명 가능한 추천 |

범위 조정은 [PRD](01_PRD.md)·ADR·계획을 함께 갱신한다. 출처 무결성·소유권·근거 부족·실패 처리는 유지한다. 모델·버전·초기 데이터 수와 배포 정책은 아직 미결정이다.

기존 machine-readable task와 신규 범위의 차이는 [하네스 연계](harness-workflow.md)를 따른다. 현재 작업은 [current-task](current-task.md)에서 확인한다.
