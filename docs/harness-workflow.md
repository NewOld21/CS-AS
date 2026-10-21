# 하네스와 제품 요구사항 연결

상태: 문서 작업 흐름. 공통 규칙은 [08_AGENTS](08_AGENTS.md)에만 둔다. 00~14가 주 문서이며 상세 자료와 실행 이력은 하위 폴더에 둔다. 문서 경로 변경 시 필수 검사와 보호 파일 참조도 함께 갱신한다.

## 에이전트가 읽을 순서

1. [문서 지도](README.md) → [PRD](01_PRD.md) → [현재 작업](current-task.md) → 해당 활성 계획.
2. 해당 영역 AGENTS.md와 [구조](05_ARCHITECTURE.md), [공개 API](api/openapi.yaml), [ERD](06_ERD.md)를 읽는다.
3. RAG 작업은 [수집](domain/ingestion.md)·[검색](domain/retrieval.md)·[답변](domain/answering.md), 생성은 [퀴즈 생성](domain/quiz-generation.md)을 추가로 읽는다.
4. [검증 기준](09_TEST_SCENARIO.md)에서 작업 요구사항의 관측 가능한 완료 증거를 선택한다.

## 요구사항 추적

| 기능 | 설계·계약 | 후속 계획 | 구현 시 필요한 증거 |
|---|---|---|---|
| FR-01/02 인증 | API auth·세션/CSRF, ERD users | 002·004 | 가입/로그인/종료·익명 거부·소유권 격리 |
| FR-03/04 퀴즈·채점 | ERD, learning, quizzes/attempts API | 004 | 정답 비노출·서버 채점·동시 멱등성 |
| FR-05/06 RAG·문맥 | RAG 구조, 내부 API, answering | 004 | “왜 틀렸어?” 문맥·근거·실패·인용 검증 |
| FR-07 기록 | ERD quiz_attempts | 004 | 재시도 중복 없음·새 풀이 누적·재로그인 복원 |
| FR-08 생성 | quiz-generation, quiz-generations API | 005 | 불량 후보 거부·근거/정답 검증·개인 문제 소유권 |
| FR-09/10 복습 | learning, me API | 005 | 통계·오답/해결 전환·구버전 결과·전체 E2E |
| FR-11/12 그래프 | knowledge-graph | 006 | 관계 의미/방향·근거·탐색 제한·Vector 대비 평가 |
| FR-13 추천 | PRD·Graph 모델 | 후속 별도 | 적은 표본·설명 가능성·사용자 이력 격리 |

각 task는 목표·allowed_paths·acceptance_criteria·out_of_scope와 검사 ID를 가진다. 구현 시 실제 기계 판독 task JSON을 만들고 검사 항목과 연결한다. 문서 계획은 그 입력이며 아직 실행 가능한 task JSON이 아니다.

## 기존 하네스와 다른 부분

현재 [harness/tasks/001-bootstrap.json](../harness/tasks/001-bootstrap.json)은 이전 RAG 단독 범위이며 인증을 제외한다. [checks.json](../harness/checks.json)은 서비스 검사가 pending이고 인증·퀴즈·복습·생성 평가를 아직 포함하지 않는다. 기존 full 통과만으로 신규 PRD 충족을 주장할 수 없다.

서비스 bootstrap의 별도 하네스 변경에서 다음을 수행한다.

- 기존 실행의 예산·상태·기록을 재사용하거나 초기화하지 않고 신규 task ID로 확장된 범위를 등록한다.
- 004/005의 allowed_paths와 기능 수용 기준을 task별로 만든다. 작업에 필요한 AGENTS/규칙 변경은 이유·검사를 따로 명시한다.
- 계약·인증·퀴즈·기록·생성·E2E·품질 검사 명령을 고정하고, 기존 검사를 유지하며 pending을 실제 검사로 교체한다.
- 하네스 엔진·권한·중단 기준을 완화하지 않는다. 새 서비스 검사가 누락된 상태에서 전체 제품 완료로 판정하지 않는다.

## 실행·완료·인계

실행 명령과 외부 state-dir는 [개발 문서](development.md)와 [검증·인계](runbooks/verification-and-handoff.md)를 따른다. 실제 검사 결과에는 코드/데이터/모델/인덱스 버전을 함께 기록한다. 링크 검사·스키마 검사·품질 검사·사람 검토의 의미를 구분한다.

이번 문서 작업은 OpenAPI 참조/인증 선언과 문서 링크를 확인한다. 서비스가 없으므로 API 동작·DB 정합성·RAG 품질은 미검증이다. 완료된 문서 계획은 completed/에 두고 current-task는 다음 planned 작업을 가리킨다.
