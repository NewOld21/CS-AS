# CS/AS

CS 퀴즈 → 질문 → 이해 → 관련 문제 → 복습을 연결하는 AI 기반 CS 학습 플랫폼입니다.
Vue/TypeScript + Spring Boot + 별도 Python/LangChain RAG + PostgreSQL/pgvector를 사용합니다. 1차는 학습 루프 전체, Graph RAG는 2차 확장입니다.

현재는 **문서·폴더·하네스 골격 단계**입니다. 서비스 코드·빌드·DB는 아직 구현하지 않았습니다.

## 시작

1. [문서 지도](docs/README.md)와 [프로젝트 제안서](docs/00_PROJECT_PROPOSAL.md)에서 방향을 확인합니다.
2. [AGENTS.md](AGENTS.md) → [공통 개발 규칙](docs/08_AGENTS.md) → 담당 영역 AGENTS.md를 읽습니다.
3. [PRD](docs/01_PRD.md)·[현재 작업](docs/current-task.md)·[구현 계획](docs/10_IMPLEMENTATION_PLAN.md)을 확인합니다.
4. [개발 명령](docs/development.md)과 [검증 시나리오](docs/09_TEST_SCENARIO.md)에 따라 작업합니다.

```sh
python3 scripts/verify.py
```

## 구조

```text
CS-AS/
├── AGENTS.md
├── Harness.md                 # docs/08_AGENTS.md 호환 포인터
├── backend/                   # Spring Boot 및 별도 ai/ Python RAG
├── frontend/                  # Vue/TypeScript
├── docs/
│   ├── 00_PROJECT_PROPOSAL.md
│   ├── 01_PRD.md
│   ├── 02_MVP_SCOPE.md
│   ├── 03_USER_FLOW.md
│   ├── 04_SCREEN_SPEC.md
│   ├── 05_ARCHITECTURE.md
│   ├── 06_ERD.md
│   ├── 07_API_SPEC.md
│   ├── 08_AGENTS.md
│   ├── 09_TEST_SCENARIO.md
│   ├── 10_IMPLEMENTATION_PLAN.md
│   ├── 11_TEAM_OWNERSHIP.md
│   ├── 12_GIT_CONVENTION.md
│   ├── 13_PHASE0_DECISIONS.md
│   ├── 14_RAG_GUIDE.md
│   ├── README.md
│   ├── AGENTS.md               # 문서 영역 진입점
│   ├── current-task.md
│   ├── development.md
│   ├── harness-workflow.md
│   ├── api/                    # OpenAPI·내부 계약·확장 후보
│   ├── domain/                 # 도메인별 상세 계약
│   ├── decisions/              # 초기 결정 이력
│   ├── runbooks/
│   └── exec-plans/{active,completed}/
├── scripts/                    # 공통 실행 진입점
└── harness/                    # 검증·정책·평가셋·상태 계약
```

[문서 지도](docs/README.md) · [공통 명령](scripts/README.md) · [하네스 사용법](harness/README.md)

bootstrap 성공은 서비스 완료를 의미하지 않습니다. full 검사는 미구현·pending이 있으면 실패하며 신규 학습 기능 검사도 추가해야 합니다.
