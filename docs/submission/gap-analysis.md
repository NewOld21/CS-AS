# 초기 Gap Analysis

기준: 2026-10-23, 사용자 요청 본문. PDF 원본은 제공되지 않아 양식·선택 항목 판정은 미확인.

| 번호 | 요구 | 초기 상태 | 확인 사항 |
|---|---|---|---|
| 1 | F2001 | IMPLEMENTED | 청킹/인덱스 manifest, 현재 예제 코퍼스와 실코퍼스 구분 필요 |
| 2 | F2002 | IMPLEMENTED | 증분 hash/벡터 재사용 구현 |
| 3 | F2003/F2004 | MISSING | 두 단계 LLM 검색 계획 없음 |
| 4 | F2004/NF2002 | IMPLEMENTED | 질의 경로 수집 호출 없음, 실측 필요 |
| 5 | F2005 | IMPLEMENTED | 청킹 설정·버전 지원 |
| 6 | F2006 | PARTIAL | max_chunks는 있으나 진단 비교 없음 |
| 7 | F2007 | MISSING | LangGraph 미사용 |
| 8 | F2008 | PARTIAL | 실제 청크 citation 검증, 본문 번호 정합 보강 필요 |
| 9 | F2007/F2008 | PARTIAL | abstention 경로 있으나 현재 demo 원문 복사 |
| 10 | F2009 | PARTIAL | DB 세션 소유권 있음, 일반 검색에는 history 미반영 |
| 11 | F2011 | MISSING | 공개 질문의 실제 metadata 조건 미지원 |
| 12 | F2010 | IMPLEMENTED | 퀴즈 AS/생성 snapshot 근거 구현 |
| 13 | F2012 | PARTIAL | 로딩/오류 있음, demo/GMS 설정 구분 부족 |
| 14 | F2012 | IMPLEMENTED | CS 학습 도메인으로 의료·금융 안내 비대상, PDF 판정 필요 |
| 15 | F2013 | PARTIAL | 퀴즈 안의 대화만 제공 |
| 16 | F2014 | MISSING | MMR 비교 없음 |
| 17 | F2015 | BLOCKED | 실제 GMS 키 없음 |
| 18 | F2015 | BLOCKED | 실제 모델 비교 결과 없음 |
| 19 | F2016 | PARTIAL | source_id/URL 있음, 유형 표시 부족 |
| 20 | NF2001 | PARTIAL | timeout 있음, 현 환경 실측 필요 |
| 21 | NF2003/NF2004 | IMPLEMENTED | 키 서버 격리·세션/CSRF·본인 조회 |
| 22 | NF2005 | IMPLEMENTED | 수집/검색/생성/provider와 Java/Vue 경계 |
| 23 | NF2006 | IMPLEMENTED | timeout/backoff/Retry-After/출처 정책 |
| 24 | NF2007 | PARTIAL | 등록부 있음, README 최신화 필요 |
| 25 | 종합 | PARTIAL | 실행별 결과 취합 필요 |
| 26 | 증빙 | MISSING | 현 작업 캡처·실행 결과 없음 |
| 27 | 제출물 | MISSING | 제출 디렉터리 없음 |
