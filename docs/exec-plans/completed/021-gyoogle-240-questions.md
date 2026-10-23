# 021 gyoogle 240문항과 존댓말

Status: completed

## 범위와 수용 기준

사용자 첨부 본문 기준: gyoogle/tech-interview-for-developer의 고정 commit Markdown만 지식 근거로 사용한다. ALGORITHM 20, COMPUTER_ARCHITECTURE 50, DATABASE 50, DATA_STRUCTURE 20, NETWORK 50, OPERATING_SYSTEM 50, EASY/MEDIUM/HARD 30/50/20%의 신규 240문항을 작성한다. 기존 15문항과 사용자 기록은 보존하므로 서비스 전체 행 수와 신규 데이터셋 수를 구분한다.

backend/ai·backend/src·frontend·scripts·docs·새 데이터/출처 고지 범위. 기존 수집 승인·쿼터·MIT·SHA를 재사용하며 새 외부 지식은 금지한다. 초안 생성과 별도 source audit를 수행하고 구조·인용·중복·수량 검증을 통과한 데이터만 seed한다. 자동 의미 검토와 사람 검토는 구분한다. 동일 seed 재실행, 채점/복습/통계 및 해당 문제의 gyoogle 전용 RAG를 검사한다.

공통 규칙의 작업 30분/모델 2 USD 및 교정 예산을 지킨다. 부족분은 근거 없는 문항으로 채우지 않고 명시한다. 공통 answer 시스템 프롬프트에는 사용자 말투 요청과 무관하게 존댓말을 사용하도록 명시하며 일반/퀴즈 AS를 함께 적용한다.

## 시작 상태

77759bf, 작업 트리 깨끗함. 기존 quiz_attempts/review_states/quiz_evidence와 서버 채점을 재사용한다. GMS/Chroma Docker 스택이 실행 중이다. 새 수집과 생성은 별도 산출물이며 기존 ACTIVE 코퍼스·사용자 DB를 초기화하지 않는다.

## 결과

고정 SHA 41a7e91356adae7ee598d5ee3c27438449ce55d8, 수집 73개/사용 69개 원문. 신규 240문항과 72/120/48 난이도 분포 검증 성공. 카테고리별 JSON 6커밋, 네 선택지 해설, blind 풀이·별도 audit 및 humanReview NOT_PERFORMED를 보존했다. 반복 거부는 다른 승인 문서로 대체했고 증거 부족 문항은 게시하지 않았다.

V12 서버 전용 source_metadata, V13 멱등 추가 seed, 기존 15문항·quiz_attempts·review_states 보존. 기존 조회·채점·학습 통계를 그대로 사용한다. 난이도 선택과 분야 내 무작위 순서를 연결했고 서버 확인 concept:gyoogle-*의 AS/관련 생성은 gyoogle 검색을 강제한다. 일반/퀴즈 공통 SYSTEM_RULES와 문제 생성 RULES에 반말 요청도 따르지 않는 존댓말 규칙을 적용했다.

검증: Java 전체 59·Python 87(Chroma 포함)·Vue 17·Chrome fixture 11·Linux 제출 사본 하네스 19 통과. 포맷/린트/타입/빌드 성공. SQL 재실행을 PostgreSQL에서 검증하고 Spring 범용 SQL splitter의 원문 backslash 파싱 오류를 실제 JDBC 실행으로 교정했다. 신규 6분야 채점→오답→정답 재풀이→복습 해결→통계→재로그인 통과. 실제 검색 인덱스 82문서/1043청크와 평가 5개 통과 후 활성화했다. Docker 5서비스 healthy와 실제 공개 255문항을 확인했다.

상세 예시·원문 목록·비용 추정·커밋은 [문제은행 보고서](../../gyoogle-question-bank.md)를 따른다. 생성·검토 보수 추정 1.953475 USD, 사람 검수는 미실행이다. 019의 실제 관련 AI 생성 happy path/상호 체크리스트 미확인은 이번 자동 회귀와 구분해 유지한다. 추가 모델 호출 없이 작업을 종료한다.
