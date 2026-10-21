# 001 저장소·문서·에이전트 구조

Status: active (로컬 구성 완료, 원격 반영 미확인)

## 목표와 범위
MAIRRY의 공통 가이드·영역별 AGENTS 패턴과 요청한 문서 구성을 CS RAG 프로젝트에 적용한다.
공통 규칙은 docs/08_AGENTS.md, API 안내는 docs/07_API_SPEC.md, 기계 계약은 docs/api/openapi.yaml, 현재 작업은 current-task, 공통 검사는 scripts로 연결한다.
앱 구현·운영 배포·외부 실행 관리자 설치는 범위 밖이다.

## 완료 조건
- [x] 루트/backend/backend/ai/frontend/docs의 AGENTS.md 연결
- [x] overview/architecture/development/testing/roadmap/domain/api/decisions/runbooks/exec-plans 구성
- [x] Java/Vue/Python 코드·테스트 위치 보존
- [x] RAG 경로를 backend/ai로 정리하고 기존 검사 연결 갱신
- [x] 문서 링크·하네스 회귀 검사 증거 기록
- [x] GitHub 반영 또는 전달 자료와 미반영 사유 기록

## 검증·인계
공통 명령: `python3 scripts/verify.py`.
전체 서비스 검사는 아직 통과 대상이 아니며 pending을 실패로 처리해야 한다.
원격 반영 결과가 확인되기 전 completed/로 이동하지 않는다.

## 실제 결과
- `python3 scripts/verify.py`: 문서 구조·내부 링크 90개와 하네스 구조 검사 통과, 회귀 테스트 19개 통과.
- 공통 task 진입점의 init → bootstrap verify → handoff를 스모크 검사한다.
- 서비스 full 프로파일은 미구현·pending 항목으로 실패하는 것이 현재 기대 결과다.
- GitHub README 생성은 403 Resource not accessible by integration으로 거부됐다. 원격 변경 없음.
- 전달 파일: CS-AS-harness.zip. 원격 반영이 막혀 active에 유지하며 002는 planned다.
- 운영 Docker·모델·DB 실행은 미검증이다.
