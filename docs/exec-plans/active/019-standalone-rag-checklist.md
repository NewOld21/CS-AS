# 019 독립 CS 챗봇과 SSAFY 27항목

Status: active

## 범위

backend/ai, backend/src, frontend, scripts, docs, README, Compose 환경 예시를 수정한다. 기존 인증·채점·학습 데이터와 승인 출처 정책은 유지한다. 30분 작업 예산 내 구현·관련 검증을 수행하며 외부 의존 미충족은 인계한다.

## 시작 상태와 Gap

89edfa6, 깨끗한 작업 트리. Docker 5개 서비스는 deterministic-test/local-dev-v1 예제 모드이며 고정 형식의 원문 복사 응답이 보이는 직접 원인이다. GMS provider는 존재하지만 현 환경에 키와 ACTIVE manifest가 없다. PDF 첨부도 없으므로 요청 본문 27개 항목을 임시 기준으로 사용한다. 기존 일반 대화 API/사용자별 저장은 구현됐으나 독립 화면, 검색 질의의 멀티턴 문맥, LangGraph, 두 단계 검색 계획, MMR/조건 필터 및 제출 패키지가 부족하다.

## 완료 기준

- /chat 독립 화면·복원·세션 격리·근거/코드·진행/오류 UI.
- 공통 LangGraph retrieve→generate, 문맥 검색·검색 계획·필터/Top-K/MMR, 근거 검증.
- 실제 Chroma 격리 컬렉션·mock GMS 계약·Spring/PostgreSQL·브라우저 회귀 증거.
- 27항목 결과/실행 명령/증거/미확인 사유와 제출 문서. 실제 GMS 및 PDF 대조는 입력이 있어야 VERIFIED 처리.

## 검증 기록

구현 및 실행 후 기록한다. 기존 개발 DB에는 테스트 회원·시도를 생성하지 않는다.

2026-10-23: 사용자가 PDF와 backend/.env를 추가했다. 원본 4쪽/27항목을 읽었으며 선택 15~19, CS 면책 비대상 14를 확인했다. 승인된 5출처 12문서/673청크를 실제 GMS text-embedding-3-large(3072차원)로 신규 색인하고 5 probe 후 ACTIVE로 전환했다. gpt-5-mini 5문항 paired 실험: 4 answered, 1 insufficient_evidence. 반복/필터 실측 21.6s/15.8s, source_id 필터 일치, count 673 유지. LLM 재작성 질의가 달라 반복 embedding은 2회였다.

Python 85(실제 Chroma 포함)·Java 56·Vue 17·Chrome fixture 13 통과, 실제 Chrome GMS 독립 멀티턴/복원/근거·퀴즈 AS 통과. Java build/cache 동시 실행 충돌은 별도 build/checklist-tests·GRADLE_USER_HOME으로 격리해 해결했다. 첫 live 인덱스 유지비 퀴즈는 코퍼스 근거 부족으로 정상 abstention; 근거를 포함한 Read Committed 퀴즈 AS를 별도 확인했다. LangGraph 기본 API는 공식 StateGraph 참조를 확인했다.

제출 패키지: docs/submission/. 최종 19 PASS / 1 FAIL / 6 UNVERIFIED / 1 NOT_APPLICABLE. 실패는 실제 생성/제출 happy path의 독립 검증 거부다. 미확인: 실제 키/인덱스 누락 격리 실행·독립 사람 정확성·지연 수용성/보안 시각 검토·종합/전체 항목 캡처. 실패/미확인을 자동 PASS로 만들지 않는다.

최종 live 확장: Read Committed 오답 AS는 출처를 반환했지만 새 후보는 EXPLANATION_OR_DISTRACTOR_UNSUPPORTED로 독립 검증에서 REJECTED됐다. READY를 요구하는 opt-in 실제 생성/제출/이력 browser 검사는 실패이며 후보 비공개 정책은 정상이다. 실제 생성 happy path는 미완료로 인계한다. 현재 키 exact scan 0건, 실제 화면에서 키/프롬프트/stack trace 비노출을 시각 확인했다. PDF 원본은 사용자가 추가한 미추적 입력으로 보존하고 임의 커밋하지 않는다.

30분 공통 작업 예산에 따라 남은 실제 생성 품질 교정·격리 오류 실행·사람/상호 점검·전체 캡처는 후속 작업이다. 계획은 active로 유지한다. 다음 실행은 저장된 거부 report와 candidate/evidence를 대조해 과도하거나 모순된 선택지를 교정하고, 같은 검증기를 유지한 채 새 요청으로 생성 happy path를 검사한다. 제출 집계는 체크리스트 각 항목의 범위이며 전체 제품 완료/모든 E2E 성공을 뜻하지 않는다.

최종 common Linux snapshot: 문서 354 links·bootstrap 설정·하네스 19개 통과. 초기 패키징 중 빠진 test-results.md 링크를 추가해 교정했다. 변경한 소스와 제출물은 단계별 커밋, 사용자 PDF와 .env는 보존한다. 개발 Docker는 새 ACTIVE 실코퍼스와 GMS로 실행하며 검사 전용 backend/DB만 종료한다.
