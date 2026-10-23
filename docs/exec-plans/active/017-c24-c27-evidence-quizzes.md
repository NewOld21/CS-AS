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
