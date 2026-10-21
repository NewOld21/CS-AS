# Harness 사용법

공통 진입점은 [scripts/README.md](../scripts/README.md), 문서 지도는 [docs/README.md](../docs/README.md)다.
공통 개발 규칙은 [08_AGENTS.md](../docs/08_AGENTS.md)에만 둔다.

## 현재 제공하는 것
- 공통 에이전트 규칙과 도구별 진입 파일
- 표준 라이브러리 기반 검사 CLI, 영속 실행 상태·이벤트·인계 파일
- 최초 검증 + 최대 3회 교정 예산, 동일 실패 연속 2회 중단, 검증 프로세스 그룹 timeout
- 독립 CI의 하네스 자체 검사, RAG 검색·출처·근거 부족 평가 도구
- 외부 실행 관리자용 정책·격리 예시와 사람 인계 절차

모델을 직접 호출하거나 코드를 자동 수정하는 데몬은 포함하지 않는다. 개발 에이전트가 실패 보고서를 받아 수정하고 다시 verify를 호출한다.
정책 JSON은 문서/설정 계약이다. 이 CLI는 범용 보안 샌드박스, 네트워크 브로커, 비용 집행기가 아니다.

## 빠른 실행 (Linux, Python 3.11+)

```sh
python3 scripts/verify.py
python3 harness/run.py init --state-dir /tmp/csas-task-001 --task harness/tasks/001-bootstrap.json
python3 harness/run.py verify --state-dir /tmp/csas-task-001 --profile bootstrap
python3 harness/run.py handoff --state-dir /tmp/csas-task-001
```

실제 긴 작업에서는 /tmp 대신 저장소 밖의 영속 볼륨을 state-dir로 사용한다. 상태 경로는 관리자만 쓰게 한다.
init은 기존 상태를 덮어쓰지 않는다. verify는 파일 잠금 안에서 실행하며 시도 횟수는 재시작해도 유지한다.
보고서에는 종료 코드·상태·시간과 실패 지문만 기록한다. 프로세스 출력은 비밀정보 누출을 줄이기 위해 저장하지 않는다.
원인 분석은 비밀정보 없는 전용 테스트 리포트를 사용한다. 실패 지문은 검사명·종료 상태 기준으로 보수적으로 계산한다.

```sh
python3 harness/run.py verify --state-dir /path/to/persistent/run --profile full
```

full은 Java/Vue/Python 구현과 고정 명령이 없으면 실패한다. pending 검사가 하나라도 있으면 통과하지 않는다.
서비스 bootstrap 후 harness/checks.json의 pending 항목을 실제 검사와 연결하는 전용 하네스 변경 작업을 한다.
필수 명령을 모두 제거하거나 bootstrap 프로파일로 서비스 완료를 주장해서는 안 된다.

## 신뢰 경계
외부 관리자는 신뢰된 기준 버전의 harness/를 /opt/harness에 읽기 전용으로 배치하고 다음처럼 실행한다.

```sh
python3 /opt/harness/run.py verify --workspace /workspace --state-dir /state/run-001 --profile full
```

후보 저장소의 run.py를 실행하면 후보가 검증기를 바꿀 수 있다. 워크플로 CI는 자체 회귀 검사이며 독립 보안 검증기를 대체하지 않는다.
CI YAML도 변경 가능한 저장소 코드다. 강제 적용은 branch protection/required checks와 외부 관리자에서 별도로 설정한다.
이 PR은 저장소 관리 설정이나 운영 인프라를 변경하지 않는다.

## 자동 교정
1. 작업 명세와 기존 실패를 확인한다.
2. 구현 후 verify한다.
3. 코드/환경/외부 서비스/정책 실패를 구분하고 가설과 증거를 handoff에 기록한다.
4. 관련 검사를 먼저 수행하고 수정 후 필수 전체 verify한다.
5. blocked이면 권한 확대나 새 run으로 예산을 우회하지 않고 인간에게 인계한다.

코드·데이터·모델·인덱스가 바뀌면 과거 검증 결과를 재사용하지 않는다. 상태의 candidate_digest는 .git과 생성물·비밀 파일을 제외한 후보 내용의 SHA-256이다.
종료 SIGKILL 등으로 running 상태가 남으면 다음 verify에서 중단 상태로 판정하고 인계한다.
30분 제한은 init 시점부터의 wall clock이며 세션을 넘어 유지된다. 모델 비용은 외부 관리자가 사전 예약·집행한다.

## RAG 평가
harness/evals/cases.jsonl은 실제 코퍼스에 연결하기 전의 seed이며 ready=false다.
문서 ID를 고정하고 평가셋을 검토한 뒤 ready=true로 바꾼다. seed 그대로 평가하면 실패한다.

```sh
python3 harness/evaluate.py --cases harness/evals/cases.jsonl --predictions /path/to/predictions.jsonl --output /path/to/report.json
```

예측 행: id, status, retrieved_document_ids, retrieved_chunk_ids, cited_chunk_ids.
실제 검색 실행에서 생성한 결과를 사용한다. 수기로 만든 예측은 evaluator 자체 테스트 외에는 품질 증거가 아니다.
검색 Recall@5 기준은 답변 가능한 문항 중 80% 이상이다. 근거 부족·출처 무결성은 전부 통과해야 한다.
공격 문서 테스트와 답변 주장-근거 일치는 서비스 통합/사람 검토가 필요하며 이 평가기만으로 판정하지 않는다.

## 인계·복원
run.py는 state.json/events.jsonl/handoff.md를 기록한다. 데이터베이스나 전체 작업 복사본은 백업하지 않는다.
외부 관리자가 git diff --binary, 미추적 파일을 포함한 snapshot, 코퍼스 manifest와 인덱스 버전을 보존한다.
복원 시 기준 커밋·정책 digest·작업 digest·코퍼스·모델·인덱스를 확인하고 검사한다.
권장 handoff 항목은 templates/handoff.md, 확장 상태 계약은 schemas/run-state.schema.json을 참고한다.
