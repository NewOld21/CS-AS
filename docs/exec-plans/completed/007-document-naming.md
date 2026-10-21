# 007 번호 기반 문서 이름과 참조 정리

Status: completed

## 목표·범위
- 사용자 요청: docs의 주 문서를 00_PROJECT_PROPOSAL.md부터 14_RAG_GUIDE.md까지 15개 이름으로 구성하고 관련 참조를 함께 수정한다.
- 기존 문서 10개를 이동하고, 범위·흐름·화면·소유권·Git 규칙 문서 5개는 기존 요구사항과 결정에서 정리한다.
- 수정 경로: docs/, 루트/영역별 에이전트 진입 문서와 README, .clinerules/, harness/check_docs.py·check.py·policy.json의 문서 경로.
- 하네스 변경 이유: 필수 문서 검사와 보호 파일 대상이 이동한 문서를 계속 검사·보호해야 한다. 검사·권한·예산 기준은 완화하지 않는다.
- 제외: 앱 기능, API 동작/스키마 변경, 원격 게시, 인원·담당자·Git 운영 설정 확정.

## 완료 조건
- [x] 요청한 15개 파일과 직관적인 내부 제목 구성.
- [x] 이동 전 문서의 본문·설계·결정 이력 보존.
- [x] 상대 링크·본문 경로·README 트리·에이전트 진입점 갱신.
- [x] 하네스 필수 문서 목록과 공통 규칙 보호 경로 갱신.
- [x] 문서·설정 검사와 이전 이름 잔여 참조 검사.
- [x] 완료 결과·환경 한계 기록 후 completed/로 이동.

## 검증 baseline
- `python -X utf8 scripts/check_docs.py`: 내부 링크 204개 통과.
- `python -X utf8 harness/check.py`: 필수 파일 17개 설정 검사 통과.
- 이전 작업에서 전체 회귀 검사는 Windows의 fcntl 부재로 실패했다. 이 환경 제한과 문서 검사 결과를 구분한다.

## 결정·인계
- README·AGENTS·개발 명령·현재 작업 및 api/domain/exec-plans 등의 상세 자료는 지원 문서로 유지한다.
- 팀 인원/개인 배정·브랜치 운영은 확정하지 않고 제안 상태를 표시한다.

## 실제 변경·검증 결과

- 기존 개요·PRD·구조·ERD·API 안내·공통 가이드·테스트·로드맵·ADR 0003·RAG 문서를 번호 이름으로 이동하고 내부 제목을 갱신했다.
- MVP 범위·사용자 흐름·화면·역할별 책임·Git 표기 문서 5개를 기존 요구사항에서 정리했다. 팀/개인 배정·Git 운영은 제안 상태다.
- api/의 OpenAPI·내부 계약과 domain/·decisions/ 초기 이력·runbooks/·실행 계획을 유지했다. 폴더별 AGENTS.md와 Harness.md는 08_AGENTS.md로 연결한다.
- Markdown 상대 링크를 문서 이동 후 위치에 맞춰 다시 계산했다. 루트 README 트리, CLAUDE/Cline/영역별 진입점과 본문 경로를 갱신했다.
- harness/check_docs.py: 15개 문서 모두 필수 목록에 포함. 하네스 구조 검사는 새 아키텍처 경로로, policy.json의 공통 규칙 보호 대상은 새 08_AGENTS.md로 이동했다. 검사/권한/예산 완화 없음.
- `python -X utf8 scripts/check_docs.py`: 문서 구조·내부 링크 238개 통과.
- `python -X utf8 harness/check.py`: 필수 설정 파일 17개 통과.
- 임시 fixture 검사: 필수 PRD 누락·깨진 링크·공통 가이드 참조 없는 adapter를 모두 거부. 임시 디렉터리는 workspace 내부에서 검사 후 정리했다.
- 추가 확인: 15개 파일/H1 제목·검사 목록 대응, 보호 경로, 기존 예산·기본 브랜치 쓰기/병합 금지 유지, OpenAPI JSON 파싱 통과.
- 이전 파일명 잔여 참조 검색: 없음. API 동작·서비스 코드는 변경하지 않았다.
- `PYTHONUTF8=1`에서 `python scripts/verify.py`: 문서/설정 검사 통과, 회귀 검사는 기존 Windows fcntl 부재로 import 실패. 전체 회귀 통과로 보고하지 않는다.

## 최종 인계

다음 작업은 002 서비스 bootstrap(planned)이다. 현재 서비스 구현은 없고 001의 원격 반영 미확인 이력은 유지한다. 현재 작업 문서에서 최신 완료를 이 계획으로 연결하고, 전체 회귀 검사는 POSIX 환경에서 수행해야 한다.
