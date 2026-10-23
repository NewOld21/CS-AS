# RAG vs no RAG

Five actual GMS gpt-5-mini pairs; same model/provider settings. RAG additionally gets approved indexed documents. Stored raw outputs: [JSON](evidence/live-comparison.json). No claim that retrieval always improves correctness. Independent human review remains UNVERIFIED.

## 1. PostgreSQL에서 Read Committed의 각 SELECT는 같은 트랜잭션 안에서 항상 같은 스냅샷을 보는가?

RAG status: answered; graph latency 19937.07 ms.

아니요. Read Committed에서는 각 SELECT는 그 쿼리가 시작된 시점의 커밋된 상태(스냅샷)를 봅니다. 따라서 같은 트랜잭션 내의 서로 다른 SELECT들은 다른 시점에 시작되면 서로 다른 결과를 볼 수 있습니다. 다만 자신의 트랜잭션에서 수행한 이전 변경은 그 다음 SELECT에서 볼 수 있습니다 [1][2].

No-RAG:

아니요. PostgreSQL의 Read Committed 모드는 "statement-level" 스냅샷을 사용하므로 같은 트랜잭션 안에서도 각 SELECT(또는 각 SQL 문)는 그 문이 실행될 때의 최신 커밋된 상태를 기준으로 별도의 스냅샷을 가져옵니다. 즉 트랜잭션 내부에서 첫 SELECT와 이어지는 두번째 SELECT는 그 사이에 다른 트랜잭션이 커밋되었다면 서로 다른 결과를 볼 수 있습니다. 단, 하나의 SQL 문(예: 복잡한 쿼리나 서브쿼리)은 그 문 내부에서는 내부적으로 동일한 스냅샷을 사용해 일관되게 동작합니다. 트랜잭션 전체에서 동일한 스냅샷을 원하면 Repeatable Read 또는 Serializable을 사용해야 합니다. (설명은 제 지식에 기반하며, 구현상 예외적 상황이나 특정 옵션이 있을 수 있어 100% 확신은 아닙니다.)

## 2. PostgreSQL Repeatable Read에서 동시 업데이트 충돌이 나면 애플리케이션은 어떻게 해야 하는가?

RAG status: answered; graph latency 13873.67 ms.

Repeatable Read에서 동시 업데이트로 인해 "could not serialize access due to concurrent update" 오류가 발생하면, 애플리케이션은 현재 트랜잭션을 중단(롤백)하고 트랜잭션 전체를 처음부터 다시 시도해야 합니다. 재시도하면 두번째 실행에서는 이미 커밋된 변경이 초기 스냅샷에 반영되므로 논리적 충돌이 사라집니다. 또한 이 격리 수준을 사용할 때는 직렬화 충돌로 인해 트랜잭션을 재시도해야 할 가능성에 대비해야 하며(단, 읽기 전용 트랜잭션은 직렬화 충돌을 일으키지 않습니다) 트랜잭션이 성공적으로 커밋될 때까지 그 안에서 읽은 데이터를 신뢰하면 안 됩니다 [1][2][3].

No-RAG:

짧게 요약하면: 동시 업데이트 충돌이 나면 애플리케이션 쪽에서 해당 트랜잭션을 안전하게 롤백하고 재시도하는 것이 일반적입니다. 다만 상황에 따라 다른 대책(락 사용, 충돌 회피, 사용자에게 충돌 알림)이 더 나을 수 있습니다. 아래에 구체적인 권장 절차와 주의사항을 정리합니다.

1) 에러 감지
- PostgreSQL의 Repeatable Read(스냅샷 격리)나 Serializable 모드에서 동시성 문제는 커밋 시점에 "could not serialize access due to concurrent update" 또는 SQLSTATE 40001(또는 데드락의 경우 40P01)을 발생시킬 수 있습니다. (정확한 메시지는 버전/상황에 따라 달라질 수 있습니다.)
- 따라서 트랜잭션 실행 중에 이 에러를 잡아야 합니다.

2) 기본 대응: 롤백 후 재시도
- 권장 패턴은 트랜잭션을 롤백하고(또는 DB 커넥션을 초기화한 뒤) 동일한 작업을 다시 시도하는 것입니다.
- 재시도 루프에는 최대 재시도 횟수와 지수적 백오프(또는 랜덤 지연)를 넣어야 합니다. 무한 루프는 피하세요.
- 재시도는 애플리케이션 레벨에서 idempotent(멱등)하도록 설계되어야 합니다. 예: 상태 플래그, 고유 요청 ID 저장 등으로 중복 적용을 방지.

예시(의사코드):
- for i in 1..MAX_RETRIES:
    begin transaction
    try:
       ... 데이터 읽기/수정 ...
       commit
       break (성공)
    except SerializationFailure (SQLSTATE 40001) or Deadlock (40P01):
       rollback
       sleep(backoff(i))
       continue
    except 다른 오류:
       rollback
       raise

3) 충돌을 줄이는 다른 전략
- 명시적 로킹: SELECT ... FOR UPDATE로 수정 대상 행을 잠그면 경쟁을 명확히 제어할 수 있습니다(동시에 접근하는 트랜잭션이 순차적으로 대기하게 됨). 성능/대기 영향 고려 필요.
- 낙관적 동시성 제어: 행에 버전 컬럼(예: updated_at 또는 version)을 두고 업데이트 시 WHERE version = :old_version 조건을 사용해 영향을 받은 행 수가 0이면 충돌로 보고 재시도.
- 작업 분해: 충돌 가능성이 높은 큰 트랜잭션을 더 작은 트랜잭션으로 쪼개거나 충돌 빈도를 낮추는 설계 변경.

4) 사용자 경험/정책적 고려
- 자동 재시도로 해결되지 않는 경우 사용자에게 충돌 사실을 알리고 수동 병합이나 재시도를 유도할 수 있습니다.
- 재시도 횟수 초과 시 적절한 에러 메시지와 로그를 남기고 운영자 개입 경로를 제공.

5) 로그와 모니터링
- 충돌 빈도와 재시도 횟수를 모니터링해 시스템 설계(데이터 모델, 트랜잭션 크기, 인덱스 등)를 개선할 근거로 삼으세요.

불확실성 고지: PostgreSQL의 동작(오류 메시지, 어떤 시점에 에러가 발생하는지)은 버전과 트랜잭션 모드에 따라 달라질 수 있습니다. 정확한 에러 코드/문구나 최적 전략은 사용 중인 PostgreSQL 버전과 애플리케이션 특성(요구 일관성, 지연 허용치, 트래픽 패턴 등)을 반영해 결정해야 합니다.

## 3. HTTP GET 요청 본문은 모든 서버와 프록시가 같은 의미로 지원하는가?

RAG status: answered; graph latency 14630.62 ms.

아니요. GET 요청에 본문을 포함하는 것은 보편적으로 같은 의미로 지원되지 않습니다. GET 요청에서 수신된 콘텐츠는 일반적으로 정의된 의미가 없고 요청의 의미나 대상(target)을 변경할 수 없으며, 일부 구현은 이를 요청 스머글링 공격 가능성 때문에 거부하고 연결을 닫을 수 있습니다. 따라서 클라이언트는 원격 서버가 사전에 본문을 허용한다고 명시하지 않는 한 GET에 본문을 생성해서는 안되며, 원본 서버만이 그러한 본문을 적절히 처리하도록 명시적으로 지원해야 합니다 [1][2].

No-RAG:

아니요. 모든 서버와 프록시는 HTTP GET 요청의 본문(body)을 동일하게 지원하지 않습니다. 일반적으로 HTTP 표준(특히 RFC 계열)은 GET에 본문을 완전히 금지하지는 않지만 그 의미와 처리는 명확히 정의되어 있지 않습니다. 결과적으로 다양한 구현체와 중간요소가 본문을 무시하거나, 삭제하거나, 전달 방식이 달라질 수 있습니다.

주요 이유 및 위험:
- 많은 서버/프레임워크(예: 일부 웹서버·라우터 라이브러리)는 GET 요청의 본문을 무시하거나 파싱하지 않습니다.
- 프록시나 캐시(예: CDN, HTTP 캐시)는 GET을 안전·멱등한 요청으로 간주해 본문 없이 캐싱·처리하도록 최적화되어 있어 본문을 버릴 수 있습니다.
- 일부 클라이언트 라이브러리나 브라우저는 GET에 본문을 보내는 것을 지원하지 않거나 비정상적으로 처리할 수 있습니다.
- 보안·로깅·라우팅 규칙 때문에 중간 장비가 본문을 차단하거나 수정할 가능성이 있습니다.

권장사항:
- GET으로 데이터를 전송해야 한다면 쿼리스트링을 사용하세요. 본문이 필요하다면 POST/PUT/PATCH 등 목적에 맞는 메서드를 사용하세요.
- 만약 반드시 GET에 본문을 사용해야 한다면(비표준적이므로) 대상 서버와 모든 중간 구성요소가 이를 안전하게 전달·처리하는지 철저히 테스트해야 합니다.

참고: 위 내용은 일반적인 관행과 구현 차이에 근거한 요약입니다. 특정 서버·프록시의 동작은 해당 제품의 문서나 환경에 따라 달라질 수 있으므로, 실제 환경에서는 직접 확인하는 것이 안전합니다.

## 4. HTTP 304 응답 본문에 새 표현 전체를 담아 보내는가?

RAG status: answered; graph latency 17225.54 ms.

아니요. 304 Not Modified 응답은 클라이언트가 이미 보유한 표현을 재사용하도록 하는 목적이며, 본문을 전송하지 않습니다. 304 응답은 헤더 섹션으로 종료되며 본문이나 트레일러를 포함할 수 없습니다[1][2].

No-RAG:

일반적으로 아니요. HTTP 304(Not Modified) 응답은 클라이언트에게 서버에 변경된 새 표현이 없음을 알리고, 클라이언트는 자신의 캐시된 표현을 그대로 사용하도록 하는 상태 코드입니다. 따라서 304 응답은 본문(body)을 포함하지 않는 것이 원칙이며(대신 ETag, Cache-Control, Expires, Vary 등 관련 헤더는 보낼 수 있음), 만약 서버가 본문을 붙여 보낸다 하더라도 클라이언트는 보통 이를 무시하고 캐시된 표현을 사용해야 합니다. 다만 구현이나 중간 프록시에 따라 예외적 동작이 있을 수 있으므로 환경에 따라 검증해 보시기 바랍니다. (내 지식은 공개 사양과 일반 구현 관행에 기반합니다.)

## 5. 문서에 근거가 없다면 2035년 PostgreSQL의 격리 수준 변경을 확정할 수 있는가?

RAG status: insufficient_evidence; graph latency 15238.13 ms.

Insufficient evidence; no cited documents.

No-RAG:

단언할 수 없습니다. 문서(공식 릴리스 노트, 커밋 기록, 개발자 메일링리스트 공지 등) 근거가 없으면 2035년에 PostgreSQL의 격리 수준(isolation level)이 바뀔 것이라고 확정할 수 없습니다. PostgreSQL의 설계·정책 변경은 오픈소스 커뮤니티(핵심 개발자, 커밋터, pgsql-hackers 토론 등)를 통해 이루어지며, 공식 경로(릴리스 노트, 커밋 로그, 위키, 공식 웹사이트의 발표)로 발표됩니다. 따라서 확인하려면 다음을 권합니다: 1) PostgreSQL 공식 릴리스 노트와 변경 로그 확인, 2) git 저장소의 커밋/머지 기록 조회, 3) pgsql-hackers, pgsql-announce 같은 메일링리스트 및 포럼 검색, 4) PostgreSQL 위키나 개발자 블로그의 제안(RFC/지도문서) 확인. 제 답변은 공개 문서를 직접 접근해 검증한 결과가 아니라 일반적인 절차와 불확실성을 기반으로 한 것이므로, 최종 판단은 공식 자료로 확인하시기 바랍니다.

## Review limits

Agent comparison: core conclusions in pairs 1, 3, 4 match the saved PostgreSQL/RFC evidence. Pair 2 correctly recommends full transaction retry, but language implying retry always eliminates all conflicts is too strong: another concurrent conflict can recur. Pair 5 abstains in both conditions. No-RAG answers in this sample did not invent source URLs, so this run does not establish a hallucination-rate advantage. Evidence presence is not full semantic correctness. Historical collection_events=0 diagnostic fields in early raw traces were constants, not measured counters; use collection counts and actual graph separation instead.
