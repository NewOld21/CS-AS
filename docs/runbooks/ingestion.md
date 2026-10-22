# CS 데이터 수집 실행

Python 3.11+, 추가 런타임 패키지 없이 저장소 루트에서 실행한다. Windows에서 python3 별칭이 없으면 `python -X utf8`을 사용한다.

```sh
# 승인 출처만 조회 (현재 빈 목록)
python3 scripts/ingest.py list
# 비활성 등록 메타데이터 포함
python3 scripts/ingest.py list --all --priority 0
# 출처/우선순위별 사전 확인: 네트워크·쓰기 없음
python3 scripts/ingest.py collect --source gyoogle --sample --dry-run
python3 scripts/ingest.py collect --priority 0 --max-documents 3 --dry-run
# 승인된 출처 수집. 현재 모두 게이트에서 제외
python3 scripts/ingest.py collect --priority 0 --sample
python3 scripts/ingest.py collect --max-documents 100
python3 scripts/ingest.py collect --source postgresql --retry-failed
```

별도 incremental 플래그 없이 매번 기존 리비전·해시를 비교한다. sample은 출처당 최대 3개, max-documents와 출처 상한 중 작은 값을 적용한다. output으로 출력 경로, registry로 별도 검토 설정을 지정한다. 기본 [등록부](../data-sources.json)는 승인 게이트를 유지한다. [수집 계약](../domain/ingestion.md)의 근거·버전·seed·허용 URL 검토 후 별도 승인한다. 현재 81개 후보의 이용 조건·robots 검토는 미완료다.

Wikipedia category 탐색은 같은 output의 catalog에 continuation과 BFS queue를 저장한다. discovery 실패 뒤 `--retry-failed`를 사용하면 마지막 성공 API 페이지 다음 continuation에서 재개한다. catalog를 삭제하거나 다른 output을 지정하면 이어받기 상태도 달라진다. 완료되지 않은 실행을 복구하려고 기존 output을 지우지 않는다. 429/일시 서버 오류는 `Retry-After`, 지수 backoff, jitter와 등록부의 `max_retries`/`timeout_seconds` 범위에서만 재시도한다.

## 오프라인 모의 샘플

```sh
python3 backend/ai/tests/sample_ingestion.py --output data/processed/ingestion-sample
python3 -m unittest discover -s backend/ai/tests -p 'test_*.py' -v
python3 -m compileall -q backend/ai/src backend/ai/tests scripts/ingest.py
python3 scripts/verify.py
```

샘플은 테스트 전용 CC0 문장/API 응답을 사용하며 실제 등록부를 변경하거나 네트워크를 호출하지 않는다. GitHub 1개, Wiki 한국어 1개·영어 1개, 공식 HTML 1개를 저장하고 재실행 시 각각 duplicate=1을 확인한다. 기존 출력에 실행하면 첫 단계부터 duplicate이므로 신규 저장 재현 시 새로운 output 경로를 사용한다.

sample-report.json에 두 실행 통계, manifest.json에 corpus_digest·객체 목록, raw에 원본, objects에 원본 참조·정제본·청크를 저장한다. 생성물은 git 제외이며 커밋된 fixture·검사로 재생성한다. 모의 출력과 라이브 코퍼스를 혼용하지 않는다.

Windows 공통 verify는 POSIX fcntl 부재로 실패할 수 있다. 문서·수집 테스트 성공을 하네스 전체 성공으로 보고하지 않는다. 최종 공통 검사는 WSL/Linux에서 수행한다. full 검사·정적 도구/DB/검색 품질 등록은 별도 bootstrap 작업이다.
