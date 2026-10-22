# 013 C14~C17 Vector 학습 루프

Status: implemented with fixtures; live corpus/model evaluation pending

## 범위

- C14: 승인 게이트를 유지한 GitHub·MediaWiki·공식 문서 수집 결과를 공통 JSONL로 export한다.
- C15: Markdown 구조 청킹, 임베딩 공급자, 버전별 ChromaDB upsert/query, 평가 후 ACTIVE 전환 gate를 구현한다.
- C16: 검색 근거만 사용하는 답변 생성, 인용 ID 검증, 근거 부족/장애 구분, 서비스 인증 내부 HTTP를 구현한다.
- C17: Spring이 본인 풀이 문맥을 복원하고 대화·인용을 저장하며 Vue가 퀴즈→채점→AS→출처 흐름을 제공한다.
- OSSU·Graph RAG·AI 문제 생성·출처 승인 변경은 제외한다.

## 구현 증거

| 단계 | 커밋 | 결과 |
|---|---|---|
| C14 | `9c12bfc` | Python 29개 통과, JSONL export. 승인 출처 0개이므로 라이브 문서 0건 |
| C15 | `0bf136b` | Python 35개(라이브 1 skip), ChromaDB 1.5.3 실제 upsert/query 1개 통과 |
| C16 | `f53dc61` | Python 41개(라이브 1 skip), 위조 인용·근거 부족·인증·deadline 검증 |
| C17 | 이 계획을 포함하는 커밋 | Spring/PostgreSQL 35개와 Checkstyle/Spotless/bootJar, Vue 단위 10개·build·lint, Playwright UI 8개 통과 |

Spring 통합은 본인 attempt의 문제·4개 선택지·선택/정답·해설·개념 복원, 타인 attempt/session 404, USER/ASSISTANT 메시지와 인용 snapshot 저장을 확인했다. 브라우저 fixture E2E는 정답 미노출 문제 선택, 멱등 키 제출, 결과 피드백, quiz/attempt ID만 사용한 세션 생성, 답변과 HTTPS 출처 링크를 확인했다.

## 미해결·후속

- `docs/data-sources.json`의 81개 출처가 모두 `usage_review=pending`, `enabled=false`이므로 라이브 문서와 운영 Chroma 청크는 0건이다. 승인 상태를 임의로 변경하지 않았다.
- OpenAI 호환 공급자는 런타임 환경변수로만 구성한다. 실제 API 키·호출·사람 답변 검토는 수행하지 않았다.
- 실제 코퍼스의 20문항 Top 5 검색 평가가 없으므로 BUILDING 인덱스를 ACTIVE로 전환하지 않았다.
- Playwright 실제 인증 API 검사는 `CSAS_E2E_API` 미지정으로 1개 skip했고, 이번 브라우저 학습 흐름은 fixture다. Spring/PostgreSQL 실제 경로는 별도 통합 테스트가 보완한다.
- 대화 목록/메시지 복원 GET, review_states·통계·AI 관련 문제는 active 004/005에 남는다.
