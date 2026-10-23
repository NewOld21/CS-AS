# 021 gyoogle 240문항과 존댓말

Status: active

## 범위와 수용 기준

사용자 첨부 본문 기준: gyoogle/tech-interview-for-developer의 고정 commit Markdown만 지식 근거로 사용한다. ALGORITHM 20, COMPUTER_ARCHITECTURE 50, DATABASE 50, DATA_STRUCTURE 20, NETWORK 50, OPERATING_SYSTEM 50, EASY/MEDIUM/HARD 30/50/20%의 신규 240문항을 작성한다. 기존 15문항과 사용자 기록은 보존하므로 서비스 전체 행 수와 신규 데이터셋 수를 구분한다.

backend/ai·backend/src·frontend·scripts·docs·새 데이터/출처 고지 범위. 기존 수집 승인·쿼터·MIT·SHA를 재사용하며 새 외부 지식은 금지한다. 초안 생성과 별도 source audit를 수행하고 구조·인용·중복·수량 검증을 통과한 데이터만 seed한다. 자동 의미 검토와 사람 검토는 구분한다. 동일 seed 재실행, 채점/복습/통계 및 해당 문제의 gyoogle 전용 RAG를 검사한다.

공통 규칙의 작업 30분/모델 2 USD 및 교정 예산을 지킨다. 부족분은 근거 없는 문항으로 채우지 않고 명시한다. 공통 answer 시스템 프롬프트에는 사용자 말투 요청과 무관하게 존댓말을 사용하도록 명시하며 일반/퀴즈 AS를 함께 적용한다.

## 시작 상태

77759bf, 작업 트리 깨끗함. 기존 quiz_attempts/review_states/quiz_evidence와 서버 채점을 재사용한다. GMS/Chroma Docker 스택이 실행 중이다. 새 수집과 생성은 별도 산출물이며 기존 ACTIVE 코퍼스·사용자 DB를 초기화하지 않는다.

## 결과

실행 후 실제 문항·파일·분포·거부·비용 추정·검증·커밋을 기록한다.
