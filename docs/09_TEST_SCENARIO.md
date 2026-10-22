# 09. TEST SCENARIO — 검증 기준·테스트 시나리오

## C22 Retrieval evaluation

- `retrieval-v1`이 20문항이며 5개 분야에 4문항씩 배분됐는지 검사한다.
- 모든 정답 문서 ID와 원문 URL이 실제 승인 코퍼스에 존재하는지 검사한다.
- 문서 Hit Rate@1/3/5, Recall@1/3/5와 MRR 계산을 고정 응답으로 단위 테스트한다.
- 문서와 청크 지표를 분리하고 청크 라벨이 없으면 `not_evaluated`로 표시한다.
- 근거 부족 문항은 검색 실패 분모에서 제외하고 사유를 보존한다.
- 실제 GMS/Chroma 평가는 별도 명령으로 실행하고 모델·차원·인덱스 버전을 결과에 남긴다.

## 현재 실행 가능한 검사

| 검사 | 명령 | 의미 |
|---|---|---|
| 문서·구조 | python3 scripts/check_docs.py | 필수 파일·내부 문서 링크 |
| 하네스 구조 | python3 harness/check.py | 설정·출처·평가 seed 형태 |
| 하네스 회귀 | python3 -m unittest discover -s harness/tests -v | 중단·예산·상태·평가 도구 |
| 공통 진입점 | python3 scripts/verify.py | 위 항목 실행 |
| 서비스 전체 | python3 scripts/verify.py --profile full --state-dir /path/to/run | 초기화된 실행 상태의 전체 검사 |

bootstrap 성공은 앱 완료가 아니다. 서비스·빌드·DB 도메인 migration은 미구현이고 [checks.json](../harness/checks.json)에 pending이 있다. 로컬 PostgreSQL·ChromaDB의 연결·영속성은 [개발 안내](development.md)의 별도 smoke로 검사한다. 기존 full에는 새 학습 기능 검사가 아직 없으므로 [하네스 연계](harness-workflow.md)의 별도 변경으로 확장해야 한다.

Linux/POSIX Python 3.11+가 기준이다. Windows에서는 문서/구조 검사를 `python -X utf8`로 실행할 수 있지만 POSIX fcntl이 필요한 하네스 회귀 검사는 WSL/컨테이너/Linux 환경이 필요하다. Windows에서 해당 검사를 건너뛴 결과를 통과로 보고하지 않는다.

## 1차 서비스에서 등록할 필수 검사

012 Vue 검사: `python scripts/frontend.py check` 및 Chrome E2E `python scripts/frontend.py e2e`. 320/390/768/1440px의 소개·로그인·가입, 키보드 지도·메뉴·dialog focus, Reduced Motion, axe WCAG AA, 로딩/중복 제출 방지·오류/연결 실패/만료를 검사한다. 실제 인증 회귀는 전용 PostgreSQL 앱과 CSAS_E2E_API를 지정해야 실행되며 설정 없이 skip한 결과를 연결 성공으로 보고하지 않는다. 012는 실제 API 포함 8개 E2E를 실행했다. [디자인 기준](design/ui-system.md)과 [개발 안내](development.md)를 따른다.

C04~C07 Java 검사: `python scripts/backend.py check` 또는 [개발 안내](development.md)의 전용 PostgreSQL Compose를 사용한다. Spotless·Checkstyle·Java 컴파일과 실제 랜덤 포트 HTTP의 migration/health·가입/중복/동시성·해시·로그인/세션 회전·만료·학습 URL 보호·CSRF·소유권/역할·로그아웃 쿠키 재전송·Secure 플래그·CORS를 검사한다. 학습 데이터 소유권 검사는 테스트 fixture이며 미구현 학습 기능의 완료 증거가 아니다. DB 통합 검사에 H2를 사용하지 않는다. 결과는 backend/build/reports/와 [011 계획](exec-plans/completed/011-c04-c07-auth.md)에 기록한다.

C09~C13 Java 검사는 같은 전용 PostgreSQL에서 V3~V5 migration, 15문항/60선택지 분포와 단일 정답, 카테고리·필터·cursor·상세, 정답/해설 비노출, 서버 채점, 다른 문제 선택지 거부, DRAFT/RETIRED, 사용자별 시도, 동일 키 재생/충돌, 동시 재전송 단일 저장과 강제 DB 실패 롤백을 검사한다. `QuizSchemaIntegrationTest`, `QuizSeedIntegrationTest`, `QuizCatalogIntegrationTest`, `QuizAttemptIntegrationTest`가 이 범위의 직접 증거다.

C14~C20 검사는 Python 50개(라이브 Chroma 조건부 1개 제외), 실제 ChromaDB 1.5.3 upsert/query 1개, Spring/PostgreSQL 전체 35개, Vue 단위 10개와 Playwright UI 8개를 수행한다. 수집 JSONL·Wikipedia 복구 탐색·공식 문서 adapter·안정 청크·인덱스 재적재, 모델/차원 불일치, 위조 인용·근거 부족·내부 인증/deadline, 본인 풀이 문맥 복원·타인 404·메시지/인용 저장, 퀴즈→채점→AS→HTTPS 출처 표시를 각각 검증한다. 외부 LLM·승인 코퍼스 품질 평가는 이 mock/fixture 검사로 대체하지 않는다.

GMS 라이브 진단은 `docker compose run --rm --no-deps ai python scripts/rag_diagnostics.py`로 실행한다. GMS Chat/Embedding, 실제 응답 차원, Chroma count, 5개 검색 질문, RAG 답변, Citation subset, 근거 부족을 PASS/FAIL/SKIP으로 기록한다. `rag_e2e.py`는 전용 로컬 계정으로 Vue proxy→Spring→RAG 전체 경로를 검증한다. 둘 다 제한된 외부 호출이며 일반 회귀 테스트와 분리한다.

Python 독립 검사: `python3 -m unittest discover -s backend/ai/tests -p 'test_*.py' -v`. 수집 정책·JSONL 외에도 Wikipedia BFS/continuation/깊이·건수·제외 범위·중복·이어받기, HTTP 429/Retry-After/timeout/비재시도 4xx, 구조 청킹·인덱스·검색·근거 답변·내부 HTTP를 검사한다. 외부 API 검사는 mock과 별도이며 기본 검사에서 라이브 호출하지 않는다. `CSAS_CHROMA_INTEGRATION=1`은 고정 클라이언트와 실제 ChromaDB가 필요하다. [샘플 실행](runbooks/ingestion.md)은 모의 응답이며 실제 코퍼스 검색 품질을 대체하지 않는다.

| 대상·기능 | 검증할 결과 |
|---|---|
| Java 정적·빌드 | 포맷·정적 분석·DTO 검증·DB migration·빌드 |
| Vue 정적·빌드 | lint·typecheck·필수 상태/컴포넌트 검사·빌드 |
| Python 정적·빌드 | Ruff·mypy·pytest·고정 의존성과 import 경계 |
| FR-01/02 인증 | 가입·로그인·세션 회전/만료·로그아웃·CSRF·익명 학습 거부·타인 소유권 거부 |
| FR-03/04 문제 | 정답/해설 비노출·4지선다/단일 정답·다른 문제 선택지 거부·서버 채점 |
| FR-07 데이터 | 같은 키의 동시 재전송 1건·다른 본문 충돌·새 키 재풀이·시도/복습 원자성·구버전 결과 보존 |
| FR-05/06 질문 | “왜 틀렸어?”에 올바른 본인 풀이 문맥·일반 대화·복원·위조 인용 거부·timeout/저장 실패 |
| FR-08 생성 | 근거 검색·JSON/단일 정답·독립 의미/근거 검증·불량 후보 비노출·멱등 생성·개인 문제 접근 |
| FR-09/10 복습 | 시도 0건 accuracy=null·재풀이 포함 통계·오답→정답→오답 상태·해결 필터·과거 해설 |
| 장애 | LLM/검색 장애 중 기존 문제/해설/이력·재풀이 가능, 오류와 근거 부족 구분 |
| 통합 | 전용 PostgreSQL + ChromaDB DB의 수집→멱등 적재→검색→답변, 채점→기록→복습 |

## 실제 RAG·생성 품질

- 실제 코퍼스와 연결한 답변 가능 20문항: Top 5 근거 적중 80% 이상.
- 근거 부족 5문항: 전부 insufficient_evidence 대응.
- 공격 문서 5개: 외부 호출·비밀정보·권한 행사 유도 실패. 검색 문서의 지시를 실행하지 않음.
- 대표 답변 5개: 사람이 주장과 인용 원문의 일치·출처·버전을 검토.
- 생성 퀴즈 출시 제안: 실제 근거로 만든 최소 20개 표본을 사람이 풀어 단일 정답·오답 선택지·해설·개념 일치를 검토. 발견한 오류는 발행 차단과 회귀 사례로 반영하고 수정 후 관련 표본을 재검토한다.
- 생성 불량 fixture: 정답 2개·정답 없음·해설 모순·인용 조작·지시 삽입 후보 모두 거부.

생성 표본 기준은 초기 출시 기본안이며 자동 검증의 정확성 보증이 아니다. 실제 평가 전에 표본 구성과 판정 기준을 고정한다. 평가 seed는 ready=false이며 실제 document_id와 연결·검토한 뒤 활성화한다. 평가 도구는 실제 서비스 검색이나 의미적 정확성을 자동 보증하지 않는다.

## 학습 루프 E2E

가입→로그인→분야 선택→검수 퀴즈 오답→해설→문맥 질문→근거 답변→관련 문제 생성→추가 풀이→마이페이지 통계/오답→재풀이→로그아웃·재로그인 후 기록 확인을 검증한다. 별도 사용자 B로 A의 시도/대화/AI 문제 접근이 거부되는지도 확인한다.

정답을 선택한 흐름, 근거 없는 질문, 생성 실패, 빈 문제/이력, 통신 오류는 각각 확인한다. UI 검사는 사용자 행동과 관찰 결과를 검증하며 구현 내부 구조를 복제하지 않는다.

## 2차 Graph 검사

관계 방향·의미·근거·VERIFIED 상태·별칭 충돌·버전·삭제/개정, 최대 2홉/크기 제한, Graph 장애 강등, Vector 단독 대비 관계 질문 평가와 1차 회귀를 추가한다. MSA→Kubernetes를 필수 관계로 표시하면 실패다.

## 증거와 완료

실제 명령·종료 코드·시각·환경·코드·코퍼스 manifest·모델·프롬프트·검증기·인덱스 버전을 실행 결과와 묶는다. 미실행·환경 실패·제품 실패를 구분한다. 문서 링크 검사는 OpenAPI 문법·Mermaid 렌더링·서비스 동작을 보증하지 않는다. 계획 완료 증거는 exec-plans/completed/에 남긴다.
