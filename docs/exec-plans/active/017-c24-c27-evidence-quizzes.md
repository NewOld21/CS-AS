# 017 C24~C27 근거 패널과 생성 퀴즈

Status: active

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
