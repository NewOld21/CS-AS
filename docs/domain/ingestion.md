# 문서 수집 도메인

상태: Python 표준 라이브러리 기반 수집·파일 staging과 공통 `normalized.jsonl`/`chunks.jsonl` export를 구현했다. 승인된 5개 출처의 실제 본문을 수집하고 별도 indexing 계층으로 ChromaDB ACTIVE 인덱스까지 검증했다. 기준 입력은 [출처 등록부](../data-sources.json) v2다. 등록부 공통 기본값은 출처별 설정에 병합하며 출처별 값이 우선한다. OSSU는 등록부·수집 계획에서 제외하고 로더도 OSSU ID·저장소를 거부하지만, 이전 결정·완료 기록은 보존한다.

2026-10-23 실측: 등록부 81개 중 Gyoogle, 한국어 Wikipedia, RFC Editor, MDN HTTP, PostgreSQL 17만 `approved`, `enabled`, `full-text`다. `data/processed/ingestion-live-v3`에는 36문서(10/13/1/10/2), staging 청크 794건이 있고 실패는 없다. 나머지 76개 출처는 승인 대기 상태로 수집하지 않는다.

## 승인 및 설정

현재 81개 출처 중 위 5개만 검토 근거·고정 버전·attribution과 함께 승인했다. 영어 Wikipedia와 나머지 공식 문서는 `enabled=false`, `usage_review=pending`, `metadata-only`를 유지한다. 등록 URL은 후보이며 승인되지 않은 항목의 이용 조건·URL 유효성 검증을 완료했다는 뜻이 아니다.

본문 수집에는 enabled=true, usage_review=approved, storage_policy=full-text, license, attribution과 review의 license_url/terms_url/robots_url/reviewed_at/body_storage_allowed=true가 필요하다. 공식 문서는 검토한 version 또는 snapshot 라벨도 필수다. 관리자가 근거를 검토한 뒤 별도 작업으로 승인하며 CLI에는 승인 우회 옵션이 없다. 공개 접근·라이선스 이름·robots 허용만으로 저장·재사용·재배포 허용을 판단하지 않는다. 본문 저장이 불가하면 metadata-only를 유지한다.

| 설정 | 의미 |
|---|---|
| priority | 0~3. P0 기초 → P1 백엔드 → P2 분산 → P3 심화. 관리자 수정 가능 |
| max_documents | 출처별 문서 상한. CLI 상한과 작은 값 적용 |
| crawl_depth | 0~5. 공식 문서 링크·Wiki 하위 카테고리 탐색 깊이 |
| request_delay_ms / timeout_seconds | 최소 요청 간격과 요청 timeout. 기본 1000ms/15초 |
| max_retries | 최초 요청 이후 일시 오류 재시도 상한. 기본 3회 |
| allowed_urls / request_urls | 문서 / API·robots·sitemap의 HTTPS host/path 허용 목록 |
| include_patterns / exclude_patterns | 디코딩한 URL 경로의 glob 필터 |
| version | 기술 버전/검토한 snapshot. latest라면 실제 버전도 기록 |
| seed_titles / seed_categories / excluded_categories | Wikipedia 초기 CS 개념·카테고리와 제외 category glob |
| seed_urls / sitemap_url | 검토한 공식 설명 문서·urlset sitemap |
| implementation_status | 공식 문서 `registered` 또는 제한 URL까지 준비된 `adapter-ready`. 승인 상태와 별개 |
| concept_mappings | native page ID/파일 경로/URL → 검수한 concept ID 목록 |

모든 HTTP redirect는 따라가기 전에 거부한다. 다른 host, 경로 접두어 위장, 자격증명 포함 URL, 인코딩된 경로 탈출을 거부한다. HTML/Markdown 다운로드 전 robots.txt를 확인하며 robots 접근 실패·거부도 성공으로 처리하지 않는다. GitHub/MediaWiki는 검토한 공식 API 범위를 사용한다. 외부 링크·이미지는 메타데이터만 보존하며 자동 다운로드하지 않는다. 원문 명령문은 데이터이며 shell로 실행하지 않는다. 네트워크 격리는 기존 외부 실행 관리자가 집행한다.

## Collector 책임

`backend/ai/src/csas_rag/ingestion/collectors.py`의 Collector(discover/fetch) 프로토콜이 확장 경계다.

- GitHub: commit SHA 고정 → tree → CS 경로 Markdown blob. README/CONTRIBUTING/index/라이선스 안내 제외, truncated tree 실패. commit·blob SHA·파일·분야 경로 보존. 저장한 문서/SHA는 blob 다운로드를 생략하며 새 SHA는 새 리비전이다.
- Wikipedia: 한·영 seed와 query/revisions API로 page ID/revision/timestamp/Wikidata ID 수집, parse oldid로 같은 리비전 본문·카테고리·관련 문서·언어 연결 보존. `categorymembers`의 page/subcat을 BFS로 순회하고 반환된 continuation 필드 전체를 다음 요청에 전달한다. 방문 category·문서 ID를 중복 제거하며 깊이·문서 수·제외 category로 범위를 제한한다. 관련 링크는 재귀 방문하지 않는다. Wikidata ID는 개념 후보 근거이며 자동 승인하지 않는다.
- 공식 문서: 명시적 seed의 HTML/Markdown, 제한된 urlset sitemap, RFC 텍스트 adapter. `adapters.py`의 공통 계약이 원문 형식·링크·추출 메타데이터를 반환하고 Collector가 허용 URL·robots·깊이·건수와 저장을 담당한다. github adapter는 공개 문서 저장소 Collector를 재사용한다. 사이트마다 adapter·허용 경로·버전·깊이·CS seed를 검토한다. 전용 공식 API가 필요한 사이트만 별도 adapter를 추가한다. 모든 공식 사이트의 전용 파서를 구현했다는 뜻이 아니다.
- RFC: 번호·Category/Status·Obsoletes/Updates 원문 보존. 후대 RFC의 대체 관계·현재 상태 검증 전에는 current_status_verified=false이며 최신 표준으로 취급하지 않는다.

공식 출처 중 RFC 9110 텍스트, 고정 commit의 MDN HTTP 저장소 Markdown, PostgreSQL 17 MVCC/transaction isolation HTML을 승인·수집했다. 나머지 75개 공식 출처는 `registered`이고 seed가 비어 있다. 정확한 버전·본문 추출 품질·license/attribution·terms·robots를 출처별로 검토하기 전에는 활성화하지 않는다. C++ 공개 안내와 유료 ISO 명세, MDN 문서와 규범 명세를 구분한다.

## 파이프라인·저장 계약

승인 → 출처별 수집 → 원본 → 추출·NFC 정규화 → 해시 비교 → 검수 개념 매핑 → 메타데이터 저장 → 청크·manifest 준비.

기본 출력 data/processed/ingestion/은 git 제외 영역이다. 파싱 전 raw에 해시별 UTF-8 원본을 저장하고 objects의 불변 JSON에 raw_uri·정제본·문서 메타데이터·청크를 저장한다. catalog.sqlite3는 배치 재개용 staging 인덱스이며 서비스 PostgreSQL을 대체하지 않는다. 서비스·계정 테이블에 쓰지 않는다. 객체를 원자적으로 쓴 뒤 SQLite 트랜잭션으로 등록한다. 파싱 실패·중단 시 미참조 원본/객체가 남을 수 있으나 manifest에는 커밋된 객체만 포함한다. 하나의 출력에는 단일 프로세스만 실행한다.

- document_id: source_id와 native key(파일 경로, Wiki page ID, 공식 URL)의 안정된 해시. concept_id와 별개다.
- revision: GitHub commit SHA, Wiki revision ID, 공식 원본 콘텐츠 SHA-256. 기술 version은 별도 필드다.
- 문서: source_id/document_id/revision/url/title/locator/language/license/attribution/content_hash/raw_hash/fetched_at/version/category/concept_ids/개념 매핑 버전/parser_version 및 출처별 metadata 보존.
- Markdown: 원문과 제목·소제목·코드 블록·이미지·링크 보존. HTML: main/article 우선, script/style/nav/header/footer 제거 후 제목·소제목·pre/code를 보존한다. 복잡한 사이트는 승인 전 표본 검토한다. 이 변경의 parser_version은 `html-markdown-v2`이며 v1 staging/인덱스를 제자리 수정하지 않고 새 output/index에서 재구축한다.
- chunk_id: 문서·리비전·parser/청크 설정·순번의 안정된 해시. chars-1200-v1은 index 준비용이며 정제본 start_char/end_char 위치를 보존한다. 검색 품질이 검증된 토큰 청킹은 후속이다.
- 문서 concept_mappings는 등록 concepts 원장과 대조한 검수 결과만 입력한다. 청크 concept_ids는 빈 배열로 준비하며 문서 태그를 무조건 전파하지 않는다. 자동 개념 추출·DB 원장 동기화는 미구현이다.
- 같은 document/revision 재수집은 duplicate다. 동일 revision의 원문 충돌은 실패한다. 다른 문서의 같은 본문은 exact_duplicate_content 표시와 함께 출처별로 보존한다. 같은 개념의 다른 설명을 제거하지 않는다.
- parser/개념 매핑 변경은 새 staging 출력에서 재구축한다. manifest에는 registry_hash·parser/청크 버전·문서 리비전·corpus_digest와 embedding_index=null을 기록한다. 같은 데이터 재실행의 corpus_digest는 같다.

## 실패·통계

문서/discovery 실패를 catalog의 failures에 보존한다. 이유는 예외 클래스/정책 코드만 남기며 응답 원문·자격증명을 로그에 넣지 않는다. 다른 문서·출처는 계속 수행한다. retry-failed는 실패 문서만 재시도하고 discovery 실패는 제한된 재탐색을 수행한다. 빈 실패 목록은 다운로드하지 않는다. 미해결 실패가 남으면 checkpoint를 전진시키지 않는다. checkpoint는 마지막 처리 리비전이며 전체 사이트 동기화 완료를 뜻하지 않는다.

Wikipedia 탐색 커서는 catalog의 `discovery_states`에 source별 JSON으로 저장한다. run_id, 시작/current category와 깊이, continuation, BFS queue, pending 문서, 방문 category, 처리 page ID/native key, 마지막 성공 위치와 오류 종류를 포함한다. API 페이지를 받은 뒤와 문서를 처리한 뒤 각각 트랜잭션 저장한다. 중단 시 같은 run_id와 continuation에서 재개하며, 처리 확인 전 중단된 문서는 다시 전달될 수 있으나 불변 revision 저장이 duplicate로 흡수한다. 설정 상한 도달 또는 queue 소진 시 complete로 닫고 다음 일반 실행은 새 run을 만든다.

HTTP 429/500/502/503/504와 네트워크/timeout만 지수 backoff와 0~0.5초 jitter로 제한 재시도한다. `Retry-After`가 더 길면 이를 우선하고 다른 4xx는 즉시 실패한다. MediaWiki 요청은 순차 실행하고 `maxlag=5`와 식별 가능한 User-Agent를 보낸다. 근거: [categorymembers](https://www.mediawiki.org/wiki/API:Categorymembers), [continuation](https://www.mediawiki.org/wiki/API:Continue), [API 예절](https://www.mediawiki.org/wiki/API:Etiquette), [Wikimedia rate limits](https://www.mediawiki.org/wiki/Wikimedia_APIs/Rate_limits).

통계: documents, 신규 success, changed, 재수집 duplicate, failed, 문서 정책 제외 excluded_policy, 출처 승인 제외 excluded_sources, elapsed_seconds, last_revision. pending 출처는 documents=0/excluded_sources=1이며 제외 문서 수를 추측하지 않는다.

## 검증·확장

명령은 [수집 실행 안내](../runbooks/ingestion.md), 증거는 [완료된 008 계획](../exec-plans/completed/008-data-ingestion.md)을 따른다. 모의 샘플은 라이브 본문 수집 성공으로 보고하지 않는다.

ChromaDB 배치는 manifest의 objects에서 문서·리비전·청크를 [ERD](../06_ERD.md)의 같은 키로 upsert한다. 모델·차원·청크 버전별 BUILDING 인덱스를 만들고 실제 코퍼스 검색·인용 평가 후 ACTIVE 전환한다. Graph는 동일 concept_id, chunk_id/revision을 근거로 검수한 관계를 투영한다. 매핑·관계 버전과 corpus_digest를 함께 남긴다. 실코퍼스 임베딩과 Chroma ACTIVE 전환은 완료했으며 PostgreSQL 원장 자동 동기화·Graph 연결은 수행하지 않는다.
