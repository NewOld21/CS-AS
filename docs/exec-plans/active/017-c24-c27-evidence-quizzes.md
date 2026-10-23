# 017 C24~C27 근거 패널과 생성 퀴즈

Status: implemented; live GMS/corpus validation pending

## 범위

frontend/, backend/src/, backend/ai/src·tests/, scripts/, docs/에서 기존 인증·검색·GMS·채점을 재사용한다. C24 → C25 → C26 → C27 순서로 검사·문서·개별 커밋을 남긴다. 후보는 C26 검증 전 공개하지 않으며 C27 저장은 검증 결과·소유권·멱등성을 확인한 단일 트랜잭션이다.

## Baseline

- 2026-10-23: 작업 시작 시 git 작업 트리 깨끗함, main 409c107.
- C23 대화와 인용 메타데이터 저장은 구현됨. 청크 본문 snapshot, 생성/검증/저장 기능은 미구현.
- Docker 이미지는 사용 가능하나 기본 Compose는 POSTGRES_PASSWORD 설정 부재로 시작 불가. 전용 테스트 Compose는 별도 사용한다. 실제 비밀값을 읽거나 출력하지 않는다.

## 완료 조건

- C24: 검증된 청크 snapshot·이전 대화 복원·접근 가능한 반응형 패널.
- C25: 등록 개념/본인 문맥과 새 검색 근거로 후보 생성. 메타데이터 추적.
- C26: 엄격 구조·인용·개념 검사와 정답을 가린 독립 풀이/해설 검증. 모호함 거부.
- C27: 검증된 개인 퀴즈 원자적 저장·멱등·기존 서버 채점·제출 후 근거.
- Python/Java/Vue/브라우저/공통 검사. 실제 GMS/Chroma 검사는 모의 검사와 구분.

## 실행 증거

각 단계에서 실제 실행 결과와 미완료 항목을 추가한다.

### C24

Docker Python 68개(66 통과·Chroma 조건부 2 skip), 전용 PostgreSQL ChatIntegrationTest 7개 통과. Vue 14개 단위·타입·production build 통과. 라이브 코퍼스/API는 환경 설정 부재로 미실행.

Chrome UI fixture 8개 통과: 저장된 청크 본문, 안전한 원문 링크, Escape 닫기·포커스 복원·390px 모바일·새로고침 복원 확인. fixture 결과를 라이브 코퍼스 성공으로 간주하지 않는다.

### C25

Docker Python 72개 중 70 통과·조건부 Chroma 2 skip. GMS mock의 JSON 후보·실제 검색 근거 ID 전달, 근거 부족 시 모델 미호출, 잘못된 JSON/provider 오류 분리, 등록 개념 입력·deadline 검증을 확인했다. 후보는 독립 검증 전 candidate=null이다. 실제 GMS 키/ACTIVE 데이터는 이 작업 환경에 제공되지 않아 라이브 호출은 미실행이다.

### C26

Docker Python 77개 중 75 통과·조건부 Chroma 2 skip. 정상 후보의 독립 3단계, 선택지 3/5개·누락·boolean 정답·중복·가짜 ID·복수 정답·정답 없음·정답 불일치·모호함·해설/오답/버전·검증 공급자 장애를 확인했다. 거부 결과에 후보 본문은 포함되지 않는다. 실제 사람 검토 표본과 GMS 의미 품질은 미검증이다.

### C27 최종 검증

| 실행 | 결과 |
|---|---|
| Docker Python unittest, CSAS_CHROMA_INTEGRATION=1 | 78개 전부 통과, skip 0. 임시 ChromaDB에 실제 upsert/query/증분/삭제 수행. 생성 모델은 mock |
| Docker 전용 PostgreSQL, gradle spotlessApply check bootJar | Spring 45개 통과, 실패/skip 0. Spotless·Checkstyle·jar 빌드 통과 |
| Vue npm run test | 15개 통과 |
| Vue npm run build / lint / format:check | 타입·production build·ESLint·Prettier 통과 |
| Chrome tests/e2e/ui.spec.ts | 8개 통과. 근거 패널→생성 버튼→생성 문제→기존 제출→제출 후 근거→새로고침 복구, 생성 POST 1회 확인 |
| Linux python3 scripts/verify.py | 문서 316개 내부 링크·설정 17개·하네스 회귀 19개 통과 |

Spring의 실제 PostgreSQL 검사는 검증된 개인 퀴즈/4선택지/개념/근거·검증 이력 저장, 정답/오답·quiz_attempts, 타인 조회 차단, 동일 키 재생·동시 키 409·모델 1회, 실패 키의 상태 코드 재생을 확인했다. 강제 옵션 INSERT 실패 시 퀴즈·근거·검증 이력이 함께 롤백되고 생성 요청만 FAILED로 남았다. 사용자 공개 응답에 후보 정답·해설·근거가 없는 것도 확인했다.

최종 Python 검사는 서비스 Bearer 인증, 다른 index 거부, 잘못된 개념 입력, 만료 deadline과 검증된 내부 HTTP 응답까지 포함한다. 실제 Chroma 통합은 격리 네트워크의 임시 /data를 사용했으며 개발/운영 볼륨을 사용하지 않았다. 고정된 requirements-local-db.lock.txt만 설치하고 외부 모델 호출은 하지 않았다.

검사 중 발견한 문제는 Java 신규 if 문의 중괄호와 Windows 체크아웃 CRLF에 따른 기존 Vue 포맷 검사였다. 중괄호를 추가하고 체크아웃의 텍스트 줄바꿈만 LF로 정규화했다. 관련 검사와 전체 검사가 통과했으며 무관한 파일의 Git 내용 변경은 없다.

## 변경 파일과 동작

- Python: generation/answering.py 본문 메타데이터, generation/quiz/ 후보와 validation.py 독립 검증, api/server.py 인증 경로, providers/llm.py 남은 timeout·재시도 0, rag_service.py/rag_dev_service.py 공급자 재사용.
- Spring: SourceResponse/RagGateway/HttpRagGateway와 ChatService snapshot, V8 migration. generation의 Controller/Service/Request/Result, V9 요청/검증/근거·발행 trigger. QuizAttemptService의 제출 후 근거. 기존 QuizCatalogService·채점 정책 재사용.
- Vue: EvidencePanel/SafeAnswer/QuizPage, quiz api와 shared client의 생성 요청 timeout. 사용자/대화별 요청 키로 GET 복구하고 중복 생성하지 않는다. 후보와 내부 검증 추론은 표시하지 않는다.
- 검사: Python test_quiz_generation.py, Java ChatIntegrationTest/GenerationIntegrationTest, Vue evidence/quiz 단위와 ui.spec.ts.
- 문서: architecture/ERD/API/RAG/answering/quiz-generation/테스트/개발/현재 작업 및 이 실행 계획.

## 예시와 거부 결과

실제 GMS 생성 예시는 확보하지 못했다. 모의 fixture 예시는 `Which statement about indexes is correct?`, 선택지는 `Indexes require maintenance on writes` / `Indexes have no storage cost` / `Indexes always speed up every write` / `Indexes replace all tables`다. 근거는 `Indexes require storage and incur maintenance costs on writes.`, 정답은 첫 선택지이며 원문 청크 chunk:1과 연결한다. 이는 모델 품질이나 승인 코퍼스의 예시가 아니다.

거부 코드는 INVALID_SCHEMA/OPTION_COUNT/DUPLICATE_OPTIONS/INVALID_CORRECT_OPTION/UNVERIFIED_CONCEPT/UNRETRIEVED_EVIDENCE, ANSWER_AMBIGUOUS_OR_UNSUPPORTED, EXPLANATION_OR_DISTRACTOR_UNSUPPORTED다. 거부 후보는 사용자 응답에 포함하지 않는다. 공급자 오류는 근거 부족으로 위장하지 않고 FAILED로 기록한다.

## 미실행·인계

- 이 작업 환경에는 backend/.env, 루트 .env, data/processed/indexes가 없다. 실제 GMS 키를 읽거나 새로 만들지 않았다. 따라서 실제 gpt-5-mini/text-embedding-3-large·승인 ACTIVE 인덱스와 연결한 전체 E2E는 미실행이다. GMS JSON 지원은 기존 provider/mock 경로로만 재사용했으며 현 환경의 라이브 지원을 새로 검증한 것은 아니다.
- 실제 코퍼스의 20문항 사람 검토와 모델 의미 정확성은 미완료다. 완료 증거가 생기기 전 계획은 active에 유지한다. 기존 016/015의 라이브 성공을 이번 변경의 성공으로 재사용하지 않는다.
- 다음 실행: 승인된 런타임 GMS·DB 설정과 ACTIVE manifest를 제공한 뒤 Compose 전체 스택에서 생성/검증/저장/채점 E2E를 제한된 1요청으로 확인한다. secret은 문서·로그·커밋에 넣지 않는다.
- 장시간 GENERATING 상태가 프로세스 종료로 남은 경우 자동 재생성하지 않는다. 요청 키로 상태를 확인하고 외부 호출 완료 여부를 확인한 후 운영자가 정리한다.
- 커밋: C24 4c70c05, C25 0b07fb9, C26 4040e72. C27은 이 기록을 포함한 `feat(quiz): support generated quiz submission` 커밋이다. 원격 push는 수행하지 않는다.
