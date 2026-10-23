# gyoogle CS 문제은행 v1

## 최종 검증 (2026-10-23)

- 신규 240문항, 난이도 EASY 72/MEDIUM 120/HARD 48, 실제 사용 원문 69개, 구조·출처·인용·독립 검토 검증 오류 0개.
- Java/PostgreSQL 전체 59개 통과, checkstyle/spotless/bootJar 성공. 6개 분야 신규 문제로 채점→오답→재풀이→통계→재로그인 및 실제 SQL 재실행 보존을 검사했습니다.
- Python 87개 모두 통과(실제 Chroma 포함), Vue 17개, Chrome fixture 회귀 11개, frontend typecheck/build/lint/format 통과.
- Linux 제출 파일 사본에서 공통 검사 19개와 문서 358개 링크 통과. Windows 직접 실행은 fcntl 미지원, 무시된 임시 clone/이전 보고서 링크로 실패했으며 규칙을 바꾸지 않고 제출 파일을 Linux에서 검사했습니다.
- 실제 GMS 임베딩 인덱스 csas-gyoogle-bank-v1: 82문서/1,043청크, 5개 검색 평가 통과. Docker 5서비스 healthy, DB 신규 240 + 기존 15 = 공개 255문항 확인.
- 문항 생성·검토는 355회 모델 응답, prompt 785,749/completion 352,650 token, 보수적 생성 비용 추정 1.953475 USD(중단 구간 예비분 포함)입니다. 실제 청구액은 아닙니다.

원문 의미를 사람에게 검수받지는 않았습니다. 관련 AI 퀴즈의 실제 모델 생성 성공과 27항목 체크리스트의 남은 검증은 기존 019 계획의 후속이며, 여기의 fixture 회귀로 완료했다고 간주하지 않습니다.

분야별 데이터 커밋: e376507(ALGORITHM), 0d3f7f9(COMPUTER_ARCHITECTURE), 51bc7b6(DATABASE), 3d1e875(DATA_STRUCTURE), 8445301(NETWORK), ba10eaf(OPERATING_SYSTEM). 시스템 존댓말 1df5712, 출처 정책 7f60d95, UI 4764af3, 시드·학습 검증 ef01133.

고정 원문 commit: `41a7e91356adae7ee598d5ee3c27438449ce55d8`.

지식 근거는 gyoogle 원문 Markdown뿐입니다. 초안과 별도 블라인드 정답 풀이·근거 검토에 GMS를 사용했습니다. 사람 의미 검수는 수행하지 않았습니다.

기존 15문항과 사용자 기록을 유지하고 신규 240문항을 CURATED로 추가합니다. reviewed_at은 자동 검토 일시이며 사람 검수 표시가 아닙니다.

| 분야 | 신규 | EASY | MEDIUM | HARD |
|---|---:|---:|---:|---:|
| ALGORITHM | 20 | 6 | 10 | 4 |
| COMPUTER_ARCHITECTURE | 50 | 15 | 25 | 10 |
| DATABASE | 50 | 15 | 25 | 10 |
| DATA_STRUCTURE | 20 | 6 | 10 | 4 |
| NETWORK | 50 | 15 | 25 | 10 |
| OPERATING_SYSTEM | 50 | 15 | 25 | 10 |

## 출처와 재현

문항에 사용한 원문 파일 수: 69. 수집한 고정 원문은 73개이며 MIT 원문과 SHA256 manifest를 data/quiz-bank/gyoogle-v1/에 보존합니다.

각 JSON 문항은 sourceRepository/sourceCommit/sourcePath/sourceUrl/sourceEvidence, topic, keywords, learningObjective, 네 선택지 해설과 독립 검토 결과를 포함합니다. 원문 내부 링크의 자료는 근거로 사용하지 않습니다.

```sh
python scripts/gyoogle_quiz_bank.py validate
python scripts/build_gyoogle_seed.py
```

컴파일러는 수량·난이도·실제 인용·출처 hash·독립 검토 중 하나라도 실패하면 V13을 만들지 않습니다. seed는 고정 UUID와 ON CONFLICT DO NOTHING으로 재실행할 수 있습니다.

## 서비스 연결

기존 퀴즈 조회·채점·quiz_attempts·오답 복습·통계 경로를 재사용합니다. source_metadata는 서버 전용이며 제출 전 API에 정답이나 해설을 노출하지 않습니다. 제출 후에는 기존 해설에 네 선택지별 해설을 함께 제공합니다.

분야별 최대 100문항 조회 및 난이도 선택, 무작위 배열로 한 바퀴 내 중복을 방지합니다. 기존 문제 URL과 ID는 유지합니다.

서버가 확인한 concept:gyoogle-* 문제의 AS와 관련 AI 생성은 planner의 제안과 무관하게 source_id=gyoogle을 강제합니다. 일반 독립 챗봇은 기존 다른 승인 출처도 사용합니다. 존댓말 규칙은 공통 시스템 프롬프트에 적용합니다.

## 사용한 원문 파일

- [Algorithm/DFS & BFS.md](https://github.com/gyoogle/tech-interview-for-developer/blob/41a7e91356adae7ee598d5ee3c27438449ce55d8/Algorithm/DFS%20%26%20BFS.md)
- [Algorithm/Hash Table 구현하기.md](https://github.com/gyoogle/tech-interview-for-developer/blob/41a7e91356adae7ee598d5ee3c27438449ce55d8/Algorithm/Hash%20Table%20%EA%B5%AC%ED%98%84%ED%95%98%EA%B8%B0.md)
- [Algorithm/HeapSort.md](https://github.com/gyoogle/tech-interview-for-developer/blob/41a7e91356adae7ee598d5ee3c27438449ce55d8/Algorithm/HeapSort.md)
- [Algorithm/LCA(Lowest Common Ancestor).md](https://github.com/gyoogle/tech-interview-for-developer/blob/41a7e91356adae7ee598d5ee3c27438449ce55d8/Algorithm/LCA%28Lowest%20Common%20Ancestor%29.md)
- [Algorithm/LIS (Longest Increasing Sequence).md](https://github.com/gyoogle/tech-interview-for-developer/blob/41a7e91356adae7ee598d5ee3c27438449ce55d8/Algorithm/LIS%20%28Longest%20Increasing%20Sequence%29.md)
- [Algorithm/MergeSort.md](https://github.com/gyoogle/tech-interview-for-developer/blob/41a7e91356adae7ee598d5ee3c27438449ce55d8/Algorithm/MergeSort.md)
- [Algorithm/QuickSort.md](https://github.com/gyoogle/tech-interview-for-developer/blob/41a7e91356adae7ee598d5ee3c27438449ce55d8/Algorithm/QuickSort.md)
- [Algorithm/Sort_Counting.md](https://github.com/gyoogle/tech-interview-for-developer/blob/41a7e91356adae7ee598d5ee3c27438449ce55d8/Algorithm/Sort_Counting.md)
- [Algorithm/Sort_Radix.md](https://github.com/gyoogle/tech-interview-for-developer/blob/41a7e91356adae7ee598d5ee3c27438449ce55d8/Algorithm/Sort_Radix.md)
- [Algorithm/간단하지만 알면 좋은 최적화들.md](https://github.com/gyoogle/tech-interview-for-developer/blob/41a7e91356adae7ee598d5ee3c27438449ce55d8/Algorithm/%EA%B0%84%EB%8B%A8%ED%95%98%EC%A7%80%EB%A7%8C%20%EC%95%8C%EB%A9%B4%20%EC%A2%8B%EC%9D%80%20%EC%B5%9C%EC%A0%81%ED%99%94%EB%93%A4.md)
- [Algorithm/다익스트라(Dijkstra).md](https://github.com/gyoogle/tech-interview-for-developer/blob/41a7e91356adae7ee598d5ee3c27438449ce55d8/Algorithm/%EB%8B%A4%EC%9D%B5%EC%8A%A4%ED%8A%B8%EB%9D%BC%28Dijkstra%29.md)
- [Algorithm/동적 계획법 (Dynamic Programming).md](https://github.com/gyoogle/tech-interview-for-developer/blob/41a7e91356adae7ee598d5ee3c27438449ce55d8/Algorithm/%EB%8F%99%EC%A0%81%20%EA%B3%84%ED%9A%8D%EB%B2%95%20%28Dynamic%20Programming%29.md)
- [Algorithm/비트마스크(BitMask).md](https://github.com/gyoogle/tech-interview-for-developer/blob/41a7e91356adae7ee598d5ee3c27438449ce55d8/Algorithm/%EB%B9%84%ED%8A%B8%EB%A7%88%EC%8A%A4%ED%81%AC%28BitMask%29.md)
- [Algorithm/최대공약수 & 최소공배수.md](https://github.com/gyoogle/tech-interview-for-developer/blob/41a7e91356adae7ee598d5ee3c27438449ce55d8/Algorithm/%EC%B5%9C%EB%8C%80%EA%B3%B5%EC%95%BD%EC%88%98%20%26%20%EC%B5%9C%EC%86%8C%EA%B3%B5%EB%B0%B0%EC%88%98.md)
- [Computer Science/Computer Architecture/ARM 프로세서.md](https://github.com/gyoogle/tech-interview-for-developer/blob/41a7e91356adae7ee598d5ee3c27438449ce55d8/Computer%20Science/Computer%20Architecture/ARM%20%ED%94%84%EB%A1%9C%EC%84%B8%EC%84%9C.md)
- [Computer Science/Computer Architecture/고정 소수점 & 부동 소수점.md](https://github.com/gyoogle/tech-interview-for-developer/blob/41a7e91356adae7ee598d5ee3c27438449ce55d8/Computer%20Science/Computer%20Architecture/%EA%B3%A0%EC%A0%95%20%EC%86%8C%EC%88%98%EC%A0%90%20%26%20%EB%B6%80%EB%8F%99%20%EC%86%8C%EC%88%98%EC%A0%90.md)
- [Computer Science/Computer Architecture/명령어 Cycle.md](https://github.com/gyoogle/tech-interview-for-developer/blob/41a7e91356adae7ee598d5ee3c27438449ce55d8/Computer%20Science/Computer%20Architecture/%EB%AA%85%EB%A0%B9%EC%96%B4%20Cycle.md)
- [Computer Science/Computer Architecture/중앙처리장치(CPU) 작동 원리.md](https://github.com/gyoogle/tech-interview-for-developer/blob/41a7e91356adae7ee598d5ee3c27438449ce55d8/Computer%20Science/Computer%20Architecture/%EC%A4%91%EC%95%99%EC%B2%98%EB%A6%AC%EC%9E%A5%EC%B9%98%28CPU%29%20%EC%9E%91%EB%8F%99%20%EC%9B%90%EB%A6%AC.md)
- [Computer Science/Computer Architecture/캐시 메모리(Cache Memory).md](https://github.com/gyoogle/tech-interview-for-developer/blob/41a7e91356adae7ee598d5ee3c27438449ce55d8/Computer%20Science/Computer%20Architecture/%EC%BA%90%EC%8B%9C%20%EB%A9%94%EB%AA%A8%EB%A6%AC%28Cache%20Memory%29.md)
- [Computer Science/Computer Architecture/컴퓨터의 구성.md](https://github.com/gyoogle/tech-interview-for-developer/blob/41a7e91356adae7ee598d5ee3c27438449ce55d8/Computer%20Science/Computer%20Architecture/%EC%BB%B4%ED%93%A8%ED%84%B0%EC%9D%98%20%EA%B5%AC%EC%84%B1.md)
- [Computer Science/Computer Architecture/패리티 비트 & 해밍 코드.md](https://github.com/gyoogle/tech-interview-for-developer/blob/41a7e91356adae7ee598d5ee3c27438449ce55d8/Computer%20Science/Computer%20Architecture/%ED%8C%A8%EB%A6%AC%ED%8B%B0%20%EB%B9%84%ED%8A%B8%20%26%20%ED%95%B4%EB%B0%8D%20%EC%BD%94%EB%93%9C.md)
- [Computer Science/Data Structure/Array vs ArrayList vs LinkedList.md](https://github.com/gyoogle/tech-interview-for-developer/blob/41a7e91356adae7ee598d5ee3c27438449ce55d8/Computer%20Science/Data%20Structure/Array%20vs%20ArrayList%20vs%20LinkedList.md)
- [Computer Science/Data Structure/Array.md](https://github.com/gyoogle/tech-interview-for-developer/blob/41a7e91356adae7ee598d5ee3c27438449ce55d8/Computer%20Science/Data%20Structure/Array.md)
- [Computer Science/Data Structure/B Tree & B+ Tree.md](https://github.com/gyoogle/tech-interview-for-developer/blob/41a7e91356adae7ee598d5ee3c27438449ce55d8/Computer%20Science/Data%20Structure/B%20Tree%20%26%20B%2B%20Tree.md)
- [Computer Science/Data Structure/Binary Search Tree.md](https://github.com/gyoogle/tech-interview-for-developer/blob/41a7e91356adae7ee598d5ee3c27438449ce55d8/Computer%20Science/Data%20Structure/Binary%20Search%20Tree.md)
- [Computer Science/Data Structure/Hash.md](https://github.com/gyoogle/tech-interview-for-developer/blob/41a7e91356adae7ee598d5ee3c27438449ce55d8/Computer%20Science/Data%20Structure/Hash.md)
- [Computer Science/Data Structure/Heap.md](https://github.com/gyoogle/tech-interview-for-developer/blob/41a7e91356adae7ee598d5ee3c27438449ce55d8/Computer%20Science/Data%20Structure/Heap.md)
- [Computer Science/Data Structure/Linked List.md](https://github.com/gyoogle/tech-interview-for-developer/blob/41a7e91356adae7ee598d5ee3c27438449ce55d8/Computer%20Science/Data%20Structure/Linked%20List.md)
- [Computer Science/Data Structure/Stack & Queue.md](https://github.com/gyoogle/tech-interview-for-developer/blob/41a7e91356adae7ee598d5ee3c27438449ce55d8/Computer%20Science/Data%20Structure/Stack%20%26%20Queue.md)
- [Computer Science/Data Structure/Tree.md](https://github.com/gyoogle/tech-interview-for-developer/blob/41a7e91356adae7ee598d5ee3c27438449ce55d8/Computer%20Science/Data%20Structure/Tree.md)
- [Computer Science/Data Structure/Trie.md](https://github.com/gyoogle/tech-interview-for-developer/blob/41a7e91356adae7ee598d5ee3c27438449ce55d8/Computer%20Science/Data%20Structure/Trie.md)
- [Computer Science/Database/Redis.md](https://github.com/gyoogle/tech-interview-for-developer/blob/41a7e91356adae7ee598d5ee3c27438449ce55d8/Computer%20Science/Database/Redis.md)
- [Computer Science/Database/SQL Injection.md](https://github.com/gyoogle/tech-interview-for-developer/blob/41a7e91356adae7ee598d5ee3c27438449ce55d8/Computer%20Science/Database/SQL%20Injection.md)
- [Computer Science/Database/SQL과 NOSQL의 차이.md](https://github.com/gyoogle/tech-interview-for-developer/blob/41a7e91356adae7ee598d5ee3c27438449ce55d8/Computer%20Science/Database/SQL%EA%B3%BC%20NOSQL%EC%9D%98%20%EC%B0%A8%EC%9D%B4.md)
- [Computer Science/Database/Transaction Isolation Level.md](https://github.com/gyoogle/tech-interview-for-developer/blob/41a7e91356adae7ee598d5ee3c27438449ce55d8/Computer%20Science/Database/Transaction%20Isolation%20Level.md)
- [Computer Science/Database/Transaction.md](https://github.com/gyoogle/tech-interview-for-developer/blob/41a7e91356adae7ee598d5ee3c27438449ce55d8/Computer%20Science/Database/Transaction.md)
- [Computer Science/Database/[DB] Anomaly.md](https://github.com/gyoogle/tech-interview-for-developer/blob/41a7e91356adae7ee598d5ee3c27438449ce55d8/Computer%20Science/Database/%5BDB%5D%20Anomaly.md)
- [Computer Science/Database/[DB] Index.md](https://github.com/gyoogle/tech-interview-for-developer/blob/41a7e91356adae7ee598d5ee3c27438449ce55d8/Computer%20Science/Database/%5BDB%5D%20Index.md)
- [Computer Science/Database/[DB] Key.md](https://github.com/gyoogle/tech-interview-for-developer/blob/41a7e91356adae7ee598d5ee3c27438449ce55d8/Computer%20Science/Database/%5BDB%5D%20Key.md)
- [Computer Science/Database/[Database SQL] JOIN.md](https://github.com/gyoogle/tech-interview-for-developer/blob/41a7e91356adae7ee598d5ee3c27438449ce55d8/Computer%20Science/Database/%5BDatabase%20SQL%5D%20JOIN.md)
- [Computer Science/Database/저장 프로시저(Stored PROCEDURE).md](https://github.com/gyoogle/tech-interview-for-developer/blob/41a7e91356adae7ee598d5ee3c27438449ce55d8/Computer%20Science/Database/%EC%A0%80%EC%9E%A5%20%ED%94%84%EB%A1%9C%EC%8B%9C%EC%A0%80%28Stored%20PROCEDURE%29.md)
- [Computer Science/Database/정규화(Normalization).md](https://github.com/gyoogle/tech-interview-for-developer/blob/41a7e91356adae7ee598d5ee3c27438449ce55d8/Computer%20Science/Database/%EC%A0%95%EA%B7%9C%ED%99%94%28Normalization%29.md)
- [Computer Science/Network/DNS.md](https://github.com/gyoogle/tech-interview-for-developer/blob/41a7e91356adae7ee598d5ee3c27438449ce55d8/Computer%20Science/Network/DNS.md)
- [Computer Science/Network/HTTP & HTTPS.md](https://github.com/gyoogle/tech-interview-for-developer/blob/41a7e91356adae7ee598d5ee3c27438449ce55d8/Computer%20Science/Network/HTTP%20%26%20HTTPS.md)
- [Computer Science/Network/OSI 7 계층.md](https://github.com/gyoogle/tech-interview-for-developer/blob/41a7e91356adae7ee598d5ee3c27438449ce55d8/Computer%20Science/Network/OSI%207%20%EA%B3%84%EC%B8%B5.md)
- [Computer Science/Network/TCP (흐름제어혼잡제어).md](https://github.com/gyoogle/tech-interview-for-developer/blob/41a7e91356adae7ee598d5ee3c27438449ce55d8/Computer%20Science/Network/TCP%20%28%ED%9D%90%EB%A6%84%EC%A0%9C%EC%96%B4%ED%98%BC%EC%9E%A1%EC%A0%9C%EC%96%B4%29.md)
- [Computer Science/Network/TCP 3 way handshake & 4 way handshake.md](https://github.com/gyoogle/tech-interview-for-developer/blob/41a7e91356adae7ee598d5ee3c27438449ce55d8/Computer%20Science/Network/TCP%203%20way%20handshake%20%26%204%20way%20handshake.md)
- [Computer Science/Network/TLS HandShake.md](https://github.com/gyoogle/tech-interview-for-developer/blob/41a7e91356adae7ee598d5ee3c27438449ce55d8/Computer%20Science/Network/TLS%20HandShake.md)
- [Computer Science/Network/UDP.md](https://github.com/gyoogle/tech-interview-for-developer/blob/41a7e91356adae7ee598d5ee3c27438449ce55d8/Computer%20Science/Network/UDP.md)
- [Computer Science/Network/[Network] Blocking Non-Blocking IO.md](https://github.com/gyoogle/tech-interview-for-developer/blob/41a7e91356adae7ee598d5ee3c27438449ce55d8/Computer%20Science/Network/%5BNetwork%5D%20Blocking%20Non-Blocking%20IO.md)
- [Computer Science/Network/[Network] Blocking,Non-blocking & Synchronous,Asynchronous.md](https://github.com/gyoogle/tech-interview-for-developer/blob/41a7e91356adae7ee598d5ee3c27438449ce55d8/Computer%20Science/Network/%5BNetwork%5D%20Blocking%2CNon-blocking%20%26%20Synchronous%2CAsynchronous.md)
- [Computer Science/Network/대칭키 & 공개키.md](https://github.com/gyoogle/tech-interview-for-developer/blob/41a7e91356adae7ee598d5ee3c27438449ce55d8/Computer%20Science/Network/%EB%8C%80%EC%B9%AD%ED%82%A4%20%26%20%EA%B3%B5%EA%B0%9C%ED%82%A4.md)
- [Computer Science/Network/로드 밸런싱(Load Balancing).md](https://github.com/gyoogle/tech-interview-for-developer/blob/41a7e91356adae7ee598d5ee3c27438449ce55d8/Computer%20Science/Network/%EB%A1%9C%EB%93%9C%20%EB%B0%B8%EB%9F%B0%EC%8B%B1%28Load%20Balancing%29.md)
- [Computer Science/Operating System/CPU Scheduling.md](https://github.com/gyoogle/tech-interview-for-developer/blob/41a7e91356adae7ee598d5ee3c27438449ce55d8/Computer%20Science/Operating%20System/CPU%20Scheduling.md)
- [Computer Science/Operating System/DeadLock.md](https://github.com/gyoogle/tech-interview-for-developer/blob/41a7e91356adae7ee598d5ee3c27438449ce55d8/Computer%20Science/Operating%20System/DeadLock.md)
- [Computer Science/Operating System/File System.md](https://github.com/gyoogle/tech-interview-for-developer/blob/41a7e91356adae7ee598d5ee3c27438449ce55d8/Computer%20Science/Operating%20System/File%20System.md)
- [Computer Science/Operating System/IPC(Inter Process Communication).md](https://github.com/gyoogle/tech-interview-for-developer/blob/41a7e91356adae7ee598d5ee3c27438449ce55d8/Computer%20Science/Operating%20System/IPC%28Inter%20Process%20Communication%29.md)
- [Computer Science/Operating System/Interrupt.md](https://github.com/gyoogle/tech-interview-for-developer/blob/41a7e91356adae7ee598d5ee3c27438449ce55d8/Computer%20Science/Operating%20System/Interrupt.md)
- [Computer Science/Operating System/Memory.md](https://github.com/gyoogle/tech-interview-for-developer/blob/41a7e91356adae7ee598d5ee3c27438449ce55d8/Computer%20Science/Operating%20System/Memory.md)
- [Computer Science/Operating System/Operation System.md](https://github.com/gyoogle/tech-interview-for-developer/blob/41a7e91356adae7ee598d5ee3c27438449ce55d8/Computer%20Science/Operating%20System/Operation%20System.md)
- [Computer Science/Operating System/PCB & Context Switcing.md](https://github.com/gyoogle/tech-interview-for-developer/blob/41a7e91356adae7ee598d5ee3c27438449ce55d8/Computer%20Science/Operating%20System/PCB%20%26%20Context%20Switcing.md)
- [Computer Science/Operating System/Page Replacement Algorithm.md](https://github.com/gyoogle/tech-interview-for-developer/blob/41a7e91356adae7ee598d5ee3c27438449ce55d8/Computer%20Science/Operating%20System/Page%20Replacement%20Algorithm.md)
- [Computer Science/Operating System/Paging and Segmentation.md](https://github.com/gyoogle/tech-interview-for-developer/blob/41a7e91356adae7ee598d5ee3c27438449ce55d8/Computer%20Science/Operating%20System/Paging%20and%20Segmentation.md)
- [Computer Science/Operating System/Process Address Space.md](https://github.com/gyoogle/tech-interview-for-developer/blob/41a7e91356adae7ee598d5ee3c27438449ce55d8/Computer%20Science/Operating%20System/Process%20Address%20Space.md)
- [Computer Science/Operating System/Process Management & PCB.md](https://github.com/gyoogle/tech-interview-for-developer/blob/41a7e91356adae7ee598d5ee3c27438449ce55d8/Computer%20Science/Operating%20System/Process%20Management%20%26%20PCB.md)
- [Computer Science/Operating System/Process vs Thread.md](https://github.com/gyoogle/tech-interview-for-developer/blob/41a7e91356adae7ee598d5ee3c27438449ce55d8/Computer%20Science/Operating%20System/Process%20vs%20Thread.md)
- [Computer Science/Operating System/Race Condition.md](https://github.com/gyoogle/tech-interview-for-developer/blob/41a7e91356adae7ee598d5ee3c27438449ce55d8/Computer%20Science/Operating%20System/Race%20Condition.md)
- [Computer Science/Operating System/Semaphore & Mutex.md](https://github.com/gyoogle/tech-interview-for-developer/blob/41a7e91356adae7ee598d5ee3c27438449ce55d8/Computer%20Science/Operating%20System/Semaphore%20%26%20Mutex.md)
- [Computer Science/Operating System/[OS] System Call (Fork Wait Exec).md](https://github.com/gyoogle/tech-interview-for-developer/blob/41a7e91356adae7ee598d5ee3c27438449ce55d8/Computer%20Science/Operating%20System/%5BOS%5D%20System%20Call%20%28Fork%20Wait%20Exec%29.md)

## 분야별 예시 2개

### ALGORITHM

**입력 문자열이 최대 100,000개일 때, 본 문서에서 제안하는 이유로 해시 테이블을 사용하는 주된 목적은 무엇입니까?** (EASY)

1. 전체 데이터(모든 입력 문자열)를 매번 탐색하지 않고, 해당 키에 해당하는 배열 영역만 확인하여 탐색 시간을 크게 줄이기 위해서입니다.
2. 문자열들을 사전순으로 정렬하여 출력하기 위해서입니다.
3. 해시를 사용하면 서로 다른 문자열이 동일한 키를 못 갖도록 충돌을 완전히 제거할 수 있기 때문에입니다.
4. 해시 테이블을 사용하면 입력의 수를 줄여 문제의 N을 실제로 작게 만들어 시간복잡도를 낮출 수 있기 때문에입니다.

정답: 1. 문서는 브루트 포스가 N^2가 되어 시간초과가 발생하므로 해시 테이블을 사용한다고 설명하며, 해시를 통해 input에 대한 key 값을 얻어 관리하면 '모든 곳을 탐색할 필요 없이 이 key에 해당하는 배열에서만 확인'하여 시간을 절약할 수 있다고 명시합니다.

출처: [Algorithm/Hash Table 구현하기.md](https://github.com/gyoogle/tech-interview-for-developer/blob/41a7e91356adae7ee598d5ee3c27438449ce55d8/Algorithm/Hash%20Table%20%EA%B5%AC%ED%98%84%ED%95%98%EA%B8%B0.md)

**DFS(깊이 우선 탐색)의 탐색 순서에 대한 설명으로 가장 알맞은 것은 무엇입니까?** (EASY)

1. 탐색 시 모든 간선을 두 번씩만 검사합니다.
2. 다음 브랜치로 넘어가기 전에, 해당 브랜치를 모두 탐색합니다.
3. 항상 인접한 노드부터 레벨 순서로 탐색합니다.
4. 방문할 노드를 큐에 넣어 먼저 들어온 순서대로 처리합니다.

정답: 2. 자료에서 DFS는 '다음 브랜치로 넘어가기 전에, 해당 브랜치를 모두 탐색'하는 방법으로 정의되어 있습니다. 즉, 한 경로를 끝까지 따라서 내려간 뒤 되돌아가 다른 브랜치를 탐색하는 방식이며 스택이나 재귀를 통해 구현한다고 명시되어 있습니다.

출처: [Algorithm/DFS & BFS.md](https://github.com/gyoogle/tech-interview-for-developer/blob/41a7e91356adae7ee598d5ee3c27438449ce55d8/Algorithm/DFS%20%26%20BFS.md)

### COMPUTER_ARCHITECTURE

**문서에 따르면 '프로세서'는 무엇을 수행하는 것으로 정의되어 있습니까?** (EASY)

1. 메모리에 저장된 명령어들을 실행하는 유한 상태 오토마톤
2. 메모리와 저장장치 사이의 데이터 전송을 관리하는 장치
3. 입력 장치의 신호를 분석해 출력 장치로 전달하는 회로
4. 운영체제의 스케줄링을 전담하는 소프트웨어 구성요소

정답: 1. 문서에서 프로세서는 '메모리에 저장된 명령어들을 실행하는 유한 상태 오토마톤'으로 정의합니다. 다른 선택지들은 메모리 전송 관리, I/O 신호 처리, 소프트웨어 구성요소와 관련된 설명으로, 문서의 정의와 일치하지 않습니다.

출처: [Computer Science/Computer Architecture/ARM 프로세서.md](https://github.com/gyoogle/tech-interview-for-developer/blob/41a7e91356adae7ee598d5ee3c27438449ce55d8/Computer%20Science/Computer%20Architecture/ARM%20%ED%94%84%EB%A1%9C%EC%84%B8%EC%84%9C.md)

**고정 소수점 표현 방식에 대한 설명으로 옳은 것은 무엇입니까?** (EASY)

1. 정수만 표현 가능하고 소수는 지원하지 않는다.
2. 소수점의 위치를 미리 정해두어 정수부와 소수부로 실수를 표현한다.
3. 가수부와 지수부로 실수를 표현하여 소수점 위치를 유동적으로 다룬다.
4. 실수를 이진 부호와 오직 지수부만으로 표현한다.

정답: 2. 정답은 고정 소수점의 정의에 따른 설명입니다. 자료에 따르면 고정 소수점은 소수점의 위치를 미리 정해놓고 정수부와 소수부로 실수를 표현하는 방식이라고 명시되어 있습니다. 다른 보기는 부동 소수점의 구성 또는 사실과 다른 설명입니다.

출처: [Computer Science/Computer Architecture/고정 소수점 & 부동 소수점.md](https://github.com/gyoogle/tech-interview-for-developer/blob/41a7e91356adae7ee598d5ee3c27438449ce55d8/Computer%20Science/Computer%20Architecture/%EA%B3%A0%EC%A0%95%20%EC%86%8C%EC%88%98%EC%A0%90%20%26%20%EB%B6%80%EB%8F%99%20%EC%86%8C%EC%88%98%EC%A0%90.md)

### DATABASE

**조인이 무엇인지 가장 정확하게 설명한 것은 무엇입니까?** (EASY)

1. 두 개 이상의 테이블이나 데이터베이스를 연결하여 데이터를 검색하는 방법입니다
2. 한 테이블의 모든 행을 다른 테이블의 컬럼으로 복사하는 방법입니다
3. 테이블의 칼럼 이름을 자동으로 변경하는 방법입니다
4. 데이터베이스의 인덱스를 재구성하는 방법입니다

정답: 1. 문서에서는 조인을 "두 개 이상의 테이블이나 데이터베이스를 연결하여 데이터를 검색하는 방법"이라고 정의하고 있습니다. 따라서 첫 번째 선택지가 조인의 기본 정의와 일치합니다. 나머지 선택지는 조인의 설명과 일치하지 않습니다.

출처: [Computer Science/Database/[Database SQL] JOIN.md](https://github.com/gyoogle/tech-interview-for-developer/blob/41a7e91356adae7ee598d5ee3c27438449ce55d8/Computer%20Science/Database/%5BDatabase%20SQL%5D%20JOIN.md)

**다음 중 트랜잭션을 구성하는 SQL 명령문 예시로 올바른 것은 무엇입니까?** (EASY)

1. BACKUP DATABASE, RESTORE DATABASE, CHECKPOINT
2. INSERT, UPDATE, DELETE, SELECT
3. CREATE DATABASE, DROP DATABASE, ALTER DATABASE
4. GRANT, REVOKE, CREATE USER

정답: 2. 문서에서 트랜잭션은 DB 상태를 변화시키기 위해 수행하는 작업 단위이며, 그 예로 SELECT, INSERT, DELETE, UPDATE와 같은 SQL 질의어를 열거하고 있습니다. 따라서 트랜잭션에 속하는 SQL 문장 예시는 INSERT, UPDATE, DELETE, SELECT입니다.

출처: [Computer Science/Database/Transaction.md](https://github.com/gyoogle/tech-interview-for-developer/blob/41a7e91356adae7ee598d5ee3c27438449ce55d8/Computer%20Science/Database/Transaction.md)

### DATA_STRUCTURE

**스택에서 최상위에 있는 값을 꺼내는 연산의 이름은 무엇입니까?** (EASY)

1. pop()
2. push()
3. enQueue()
4. deQueue()

정답: 1. 자료에서 '데이터 최상위 값 뺌 : pop()'으로 설명되어 있으므로 최상위 값을 꺼내는 연산은 pop()입니다.

출처: [Computer Science/Data Structure/Stack & Queue.md](https://github.com/gyoogle/tech-interview-for-developer/blob/41a7e91356adae7ee598d5ee3c27438449ce55d8/Computer%20Science/Data%20Structure/Stack%20%26%20Queue.md)

**C++에서 정적 배열 arr[]의 요소 개수를 구하기 위해 다음 코드 int n = sizeof(arr) / sizeof(arr[0]); 를 사용하였습니다. 이 표현식이 정확한 이유로 옳은 것은 무엇입니까?** (EASY)

1. sizeof(arr[0])는 항상 4를 반환하므로 모든 배열에서 이를 나누면 요소 개수를 구할 수 있다.
2. sizeof(arr)는 배열 전체 바이트 수이고 sizeof(arr[0])는 한 요소의 바이트 수이므로 둘을 나누면 요소 개수가 된다.
3. sizeof(arr)는 배열의 요소 개수를 반환하고 sizeof(arr[0])는 첫 요소의 값 자체를 반환하므로 나누면 요소 개수가 된다.
4. sizeof(arr)는 포인터 크기를 반환하므로 배열 요소 개수를 구하려면 포인터 산술과 함께 사용해야 한다.

정답: 2. 소스에는 int arr[] = { ... }; 와 함께 int n = sizeof(arr) / sizeof(arr[0]); // 7 과 같이 배열 전체 크기를 한 요소의 크기로 나누어 요소 수를 얻는 예제가 제시되어 있습니다. 즉 sizeof(arr)는 배열 전체 바이트 수이고 sizeof(arr[0])는 한 요소의 바이트 수이므로 나눗셈으로 요소 개수를 얻습니다.

출처: [Computer Science/Data Structure/Array.md](https://github.com/gyoogle/tech-interview-for-developer/blob/41a7e91356adae7ee598d5ee3c27438449ce55d8/Computer%20Science/Data%20Structure/Array.md)

### NETWORK

**TCP에서 수신 윈도우(Receive Window)는 무엇을 나타내며, 송신자는 그것을 어떻게 사용합니까?** (EASY)

1. 수신자의 남은 수신 버퍼 용량을 나타내며, 송신자는 이를 확인해 버퍼를 초과하지 않도록 전송량을 조절합니다.
2. 송신자가 보낼 수 있는 최대 세그먼트 크기(MSS)를 나타내며, 송신자는 항상 이 크기로 세그먼트를 분할해 보냅니다.
3. 네트워크 혼잡도를 나타내는 값이며, 송신자는 이 값을 보고 전송 속도를 지수적으로 증가시킵니다.
4. 패킷 손실률을 나타내는 지표이며, 송신자는 손실률이 높으면 전송을 중지합니다.

정답: 1. 본문은 수신자가 자신의 수신 버퍼의 남은 용량을 송신자에게 알리는 것을 '수신 윈도우'라고 설명하고, 송신자는 그 값을 확인하여 수신 버퍼 용량을 초과하지 않도록 전송한다고 명시합니다(라인 31-35). 따라서 수신 윈도우는 남은 버퍼 용량을 나타내며 송신자는 이를 기준으로 전송량을 조절합니다.

출처: [Computer Science/Network/TCP (흐름제어혼잡제어).md](https://github.com/gyoogle/tech-interview-for-developer/blob/41a7e91356adae7ee598d5ee3c27438449ce55d8/Computer%20Science/Network/TCP%20%28%ED%9D%90%EB%A6%84%EC%A0%9C%EC%96%B4%ED%98%BC%EC%9E%A1%EC%A0%9C%EC%96%B4%29.md)

**UDP(User Datagram Protocol)에 대해 옳은 설명은 무엇입니까?** (EASY)

1. 응용 계층 프로토콜로 DNS 같은 서비스를 직접 규정하는 규약입니다.
2. 비연결형이며 신뢰성을 보장하지 않는 전송 계층 프로토콜입니다.
3. 연결을 설정한 후 순서 보장과 재전송으로 신뢰성을 제공하는 전송 계층 프로토콜입니다.
4. 네트워크 계층에서 라우팅과 패킷 분할을 담당하는 프로토콜입니다.

정답: 2. 문서에서 UDP는 '비연결형, 신뢰성 없는 전송 프로토콜'이며 전송 계층(Transport layer)에서 동작한다고 명시되어 있습니다. 따라서 비연결성·비신뢰성·전송 계층이라는 속성이 맞습니다.

출처: [Computer Science/Network/UDP.md](https://github.com/gyoogle/tech-interview-for-developer/blob/41a7e91356adae7ee598d5ee3c27438449ce55d8/Computer%20Science/Network/UDP.md)

### OPERATING_SYSTEM

**메인 메모리(main memory)에 대해 옳은 설명은 무엇입니까?** (EASY)

1. 메인 메모리는 CPU가 직접 접근하는 기억 장치이며, 프로세스가 실행되려면 프로그램이 메모리에 올라와야 합니다.
2. 메인 메모리는 디스크처럼 영구 저장을 위해 설계되어, 전원이 꺼져도 데이터가 유지됩니다.
3. 메인 메모리는 캐시보다 느리지만 보통 레지스터보다 더 빠르게 접근할 수 없도록 설계됩니다.
4. 메인 메모리는 CPU가 직접 명령어를 생성하여 프로그램을 작성하는 장치입니다.

정답: 1. 본문은 메인 메모리를 'CPU가 직접 접근할 수 있는 기억 장치'라고 정의하고, '프로세스가 실행되려면 프로그램이 메모리에 올라와야 함'을 명시하고 있습니다(라인 3–5). 따라서 옵션 1이 정답입니다.

출처: [Computer Science/Operating System/Memory.md](https://github.com/gyoogle/tech-interview-for-developer/blob/41a7e91356adae7ee598d5ee3c27438449ce55d8/Computer%20Science/Operating%20System/Memory.md)

**wait() 시스템콜의 역할로 옳은 것은 무엇입니까?** (EASY)

1. 자식 프로세스를 백그라운드로 전환하여 즉시 반환한다.
2. 부모 프로세스가 자식 프로세스의 종료를 기다리게 한다.
3. 자식 프로세스가 부모 프로세스의 종료를 기다리게 한다.
4. 새로운 프로세스를 생성하여 부모와 자식이 동시에 종료되도록 한다.

정답: 2. 본문은 wait가 “child 프로세스가 종료될 때까지 기다리는 작업”이라고 분명히 설명합니다. 또한 wait()는 child가 끝나기 전에는 return하지 않으므로 부모가 자식의 종료를 기다리게 함을 명시하고 있습니다.

출처: [Computer Science/Operating System/[OS] System Call (Fork Wait Exec).md](https://github.com/gyoogle/tech-interview-for-developer/blob/41a7e91356adae7ee598d5ee3c27438449ce55d8/Computer%20Science/Operating%20System/%5BOS%5D%20System%20Call%20%28Fork%20Wait%20Exec%29.md)

