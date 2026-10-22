# 008 CS 데이터 수집

Status: completed (live collection remains approval-gated)

## 범위와 완료 조건

- 허용 경로: backend/ai/, scripts/ingest.py, docs/. 사용자 기존 변경 보존.
- GitHub, 한·영 MediaWiki, 공식 문서 adapter와 승인 게이트, 제한된 CLI 구현.
- 원본/정제본/메타데이터, 불변 리비전·청크, 증분·중복·부분 실패 재시도 검증.
- 출처 등록부 확장, OSSU 현재 수집 정책에서 제거. 승인 대기·비활성 유지.
- 모의 API 샘플과 단위 검사, 공통 verify 실행 결과·환경 제약 기록.
- ChromaDB 인덱싱 경로는 C15에서 구현했다. 승인 코퍼스 적재와 Graph 투영은 후속이며 서비스 PostgreSQL을 수집 staging으로 사용하지 않는다.

## Baseline

- 2026-10-21: AI 수집 코드 없음. backend/.env.example은 기존 미추적 사용자 파일.
- Windows python3 실행 불가. 공통 verify는 POSIX 환경 필요. 사용 가능한 Python으로 별도 검사 예정.

## 검증 및 인계

2026-10-21, Windows/Python 3.12.10에서 아래를 수행했다.

| 실행 | 결과 |
|---|---|
| python3 scripts/verify.py | Windows python3 실행 별칭 오류, 실행 시작 불가 |
| python -X utf8 scripts/verify.py | 문서 통과. 자식 프로세스 cp949 디코딩 오류 및 POSIX fcntl 부재로 실패 |
| PYTHONUTF8=1; python -X utf8 harness/check.py | bootstrap 설정 17개 검사 통과 |
| PYTHONUTF8=1; python -X utf8 scripts/verify.py 최종 실행 | 문서/내부 링크 251개·설정 17개 통과, 하네스 회귀는 fcntl 부재로 실패 (verify 종료 코드 1) |
| git diff --check | 통과 |
| python -X utf8 -m unittest discover -s backend/ai/tests -p 'test_*.py' -v | 28개 통과, 실패 0 |
| python -X utf8 -m compileall -q backend/ai/src backend/ai/tests scripts/ingest.py | 통과 (문법 검사이며 Ruff/mypy를 대체하지 않음) |
| python -X utf8 backend/ai/tests/sample_ingestion.py --output data/processed/ingestion-sample-v1 | 아래 모의 샘플 저장·재수집 성공 |
| python -X utf8 scripts/ingest.py collect --priority 0 --sample --dry-run | P0 10개 출처 승인 게이트 제외, 문서·네트워크·쓰기 0 |
| CLI collect --sample 전체 실행 | 81개 출처 승인 게이트 제외, 문서·실패 0, catalog 생성 없음 |

2026-10-22 C14 증거: 커밋 `9c12bfc`, 공통 `normalized.jsonl`·`chunks.jsonl` 원자 export 추가, Python 전체 29개 통과. 등록부 81개가 모두 pending이므로 라이브 문서 수집 0건을 유지했다.

2026-10-22 C18: 등록부 v2에 공통 재시도·timeout 기본값을 추가하고 GitHub·한/영 MediaWiki·공식 문서별 필수 설정을 fail-closed 검증한다. OSSU ID·저장소 설정은 로더에서 거부한다. 저장소와 `data/`에서 기존 OSSU 수집 데이터는 발견되지 않았으며 어떤 데이터도 삭제하지 않았다.

2026-10-22 C19: 한/영 Wikipedia의 categorymembers continuation·BFS·깊이/건수/제외 category를 구현했다. SQLite discovery_states에 run ID, queue/cursor, 방문 category, 처리 문서 ID, 마지막 성공과 실패 위치를 저장한다. HTTP transport는 설정 timeout, 429/5xx/네트워크 제한 재시도, 지수 backoff+jitter와 Retry-After를 적용하고 다른 4xx는 재시도하지 않는다. 공식 MediaWiki categorymembers/continuation/API etiquette/rate-limit 문서를 기준으로 `maxlag=5`와 식별 User-Agent를 적용했다.

2026-10-22 C20: 공식 HTML/Markdown/RFC/urlset sitemap을 공통 adapter 계약으로 분리하고 HTML heading/pre/code 보존을 추가해 parser를 html-markdown-v2로 올렸다. RFC 9110, MDN HTTP Markdown, PostgreSQL 17의 제한 URL 3개를 adapter-ready 후보로 표시했지만 모두 pending·비활성이라 라이브 본문은 0건이다. 모의 승인 fixture로 원문/제목/heading/code/version/license/URL, 변경 revision, JSONL→기존 C15 build_index 호환을 검증한다.

2026-10-22 최종 검증:

| 실행 | 결과 |
|---|---|
| Python 3.11 `python -m unittest discover -s backend/ai/tests -p test_*.py -v` | 총 50개: 49개 통과, 실제 Chroma 조건부 1개 skip |
| Python 3.11 모의 sample ingestion | GitHub/Wiki ko/Wiki en/official 각 신규 1, 재실행 duplicate 1, 실패 0 |
| `scripts/ingest.py collect --priority 0 --sample --dry-run` | P0 10개 모두 승인 게이트 제외, 네트워크·쓰기·본문 0 |
| Linux `python scripts/verify.py` | 문서/내부 링크 309개, bootstrap 설정 17개, harness 19개 통과 |
| `git diff --check` | 통과 |

모의 결과:

| 출처 | 신규 | 재수집 중복 | 변경 | 실패 | 정책 제외 |
|---|---|---|---|---|---|
| fixture-github | 1 | 1 | 0 | 0 | 0 |
| fixture-wiki-ko | 1 | 1 | 0 | 0 | 0 |
| fixture-wiki-en | 1 | 1 | 0 | 0 | 0 |
| fixture-official-docs | 1 | 1 | 0 | 0 | 0 |

- 최종 C20 모의 corpus_digest: `b4059724af36b5b837715dc4f38b3a1ac25e495d022efabd88057aec1440661f`.
- corpus parser: html-markdown-v2, chunks: chars-1200-v1, registry: v2, embedding_index: null.
- 생성물: data/processed/ingestion-sample-v1/의 sample-report.json, manifest.json, raw/, objects/, catalog.sqlite3. git 제외, 커밋된 fixture로 재생성 가능.
- 실제 본문 수집 성공 출처: 없음. gyoogle/Wikipedia 한·영/공식 78개 전부 pending이며 승인·enabled 상태를 변경하지 않았다. 제외 문서 수는 미탐색으로 0이며 81은 제외된 출처 수다.
- GitHub 후보 저장소 페이지의 MIT 표시와 MediaWiki revisions API 문서를 읽기 전용으로 확인했다. 전체 출처의 약관·robots·저장/재배포 검토가 완료된 것은 아니다. [GitHub 후보](https://github.com/gyoogle/tech-interview-for-developer), [MediaWiki API](https://www.mediawiki.org/wiki/API:Revisions).
- 기존 backend/.env.example 사용자 파일은 수정하지 않았다. harness/·CI·평가 seed도 수정하지 않았다. docs/08_AGENTS.md는 요청된 OSSU 제외 정책 한 줄만 갱신했다.

## 후속 작업

1. 관리자가 P0 출처별 라이선스·저작자 표시·약관·robots·버전·CS seed·본문 추출 품질을 검토한 뒤 승인한다. 그 후 별도 output에서 라이브 샘플을 실행한다. 현재 승인 없이 라이브 본문 수집을 시도하지 않는다.
2. MDN 후보의 `main`을 검토한 commit SHA로 고정하고 RFC의 IETF Trust 조건과 PostgreSQL 문서 저장·재사용 범위를 확인한다.
3. 사이트 전용 API가 필요한 경우 Collector adapter를 확장한다. 현재 공식 HTML/Markdown/sitemap/RFC/공개 GitHub 저장소 전략과 모의 샘플 검증만 완료했다.
4. parser v2 승인 corpus를 새 BUILDING 인덱스에 적재하고 실제 Chroma/검색 품질 평가 후 ACTIVE로 전환한다. 기존 v1 staging·인덱스는 삭제하지 않는다.

실행 방법과 상세 저장 계약은 [수집 안내](../../runbooks/ingestion.md), [도메인](../../domain/ingestion.md)을 따른다.
