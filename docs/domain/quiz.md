# Quiz domain

상태: C10~C13 정적 검수 문제 은행 구현. AI 생성 문제는 [quiz-generation](quiz-generation.md)의 후속 범위다.

## 원장과 발행

PostgreSQL `concepts.id`가 공통 개념 식별자의 원장이다. 문제는 `quiz_concepts`로 하나 이상의 개념에 연결하고 대표 개념은 정확히 하나다. CURATED 문제는 소유자가 없고 AI_GENERATED 문제는 사용자 소유자가 필수다. 공개 가능한 READY 문제는 해설·검수 시각·출처 URL, 서로 다른 4개 선택지와 정확히 하나의 정답을 가져야 한다. PostgreSQL 지연 제약 트리거가 선택지 수·정답 수·대표 개념을 커밋 시점에 검사한다.

초기 V4 데이터는 고정 UUID와 안정된 concept ID를 사용한 15문항이다. 분포는 운영체제 3, 네트워크 3, 데이터베이스 3, 자료구조 2, 알고리즘 2, 컴퓨터 구조 2다. 각 문항은 Linux man-pages/POSIX, RFC Editor, PostgreSQL, NIST DADS, RISC-V 명세에서 해당 사실을 확인한 뒤 독자적인 질문·선택지·해설로 작성했다.

## 조회와 채점

인증된 사용자는 CURATED 또는 본인 소유 READY 문제만 조회한다. 공개 DTO에는 `is_correct`, 정답 ID, 해설, 출처/검수 메타데이터가 없다. 목록은 ID 오름차순이며 불투명 cursor는 분야·난이도·개념 필터에 묶인다.

제출은 세션 사용자, 경로 quiz ID, 본문의 selected option ID와 사용자 범위 UUID 멱등 키만 신뢰한다. 서버가 문제 상태·선택지 소속·정답을 조회하고 한 트랜잭션에서 `quiz_attempts`를 저장한다. `(user_id, idempotency_key)` UNIQUE와 충돌 없는 insert로 동시 재전송을 한 행으로 수렴시킨다. 같은 키·같은 정규화 요청은 원래 결과를 재생하고 다른 요청은 409다. 문제 ID·정답 선택지·해설·출처 URL은 시도 시점에 연결 또는 스냅샷으로 보존한다.

상세 API와 오류는 [공개 계약](../api/openapi.yaml), 관계와 인덱스는 [ERD](../06_ERD.md), 실행 검사는 [검증 기준](../09_TEST_SCENARIO.md)을 따른다.
