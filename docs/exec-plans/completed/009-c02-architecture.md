# 009 C02 아키텍처·API 결정

Status: completed

## 범위·완료 조건

사용자 C02 요청. allowed_paths: docs/. 스택 ADR·서비스 책임·REST 오류·인증/인가를 기록하고 기존 설계와 동기화한다. 하네스 정책과 사용자 환경 파일은 변경하지 않는다. 0001 번호 충돌은 새 ADR 0004로 해결한다.

- [x] architecture.md와 ADR 0004 작성.
- [x] OpenAPI 오류 DTO와 현재 설계 동기화.
- [x] 문서·계약 검사 증거와 독립 커밋.

## Baseline·인계

2026-10-21 Windows / Python 3.12.10. 시작 브랜치 feat/008-data-ingestion, 사용자 untracked backend/.env.example 존재(보존).
`python -X utf8 scripts/verify.py`: 문서 검사 PASS, 자식 Python의 cp949 디코딩 및 POSIX fcntl 부재로 exit 1. 환경 실패이며 하네스는 수정하지 않는다.
C03는 별도 계획으로 실행한다. 기존 008 수집 계획은 미완료 상태를 유지한다.

## 완료 증거

`PYTHONUTF8=1` 환경에서 `python -X utf8 scripts/check_docs.py`: exit 0, 271 내부 링크 PASS. `python -X utf8 harness/check.py`: exit 0, bootstrap 구조 PASS. `python -X utf8 -m unittest discover -s backend/ai/tests -p 'test_*.py' -q`: exit 0, 기존 수집 28 tests PASS. `git diff --check`: exit 0. 별도 OpenAPI 참조 점검의 shell one-liner는 인용 오류로 실패했으며 최종 계약 검증은 C03 증거에서 재수행한다. 서비스 인증·전역 예외 처리 구현은 이번 범위가 아니다.
