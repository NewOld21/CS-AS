# CS/AS 인터랙티브 학습 공간

상태: 2026-10-21 실제 레퍼런스 관찰과 Vue 구현. 기준은 [화면 명세](../04_SCREEN_SPEC.md), 범위·검증은 [실행 계획](../exec-plans/completed/012-reference-ui.md)이다.

## 실제 확인한 레퍼런스

[La Caisse](https://www.la-caisse-jeu-simulation.com/)를 Chrome으로 직접 확인했다. 웹 텍스트 추출 도구는 실패했으나 실제 브라우저는 HTTP 200이었다. 1440×960와 390×844의 스크린샷·계산 스타일·Web Animations API를 관찰했다. 원본 자산·로고·캐릭터·CSS/JavaScript를 제품에 복사하지 않았다.

| 조사 | 실제 관찰 | CS/AS의 독자적 적용 |
|---|---|---|
| 메인 배치 | 중앙 상단 픽셀 로고, 우주 장면/부유 섬, 하단 안내문과 Commencer 버튼 | 큰 한국어 메시지와 CTA, 직접 선택하는 CS 궤도 지도 |
| 배경·색 | 어두운 남색 우주·별, 청록/분홍/보라 소용돌이, 흰 글자 | 남색/회백색+연두, 분야별 파랑·보라·살구 |
| 타이포 | ARI-W9500 monospace. 본문 desktop 18px/mobile 14px, CTA 16px. 화면의 픽셀 로고와 DOM h1은 별개 | 한국어 시스템 sans, 짧은 좌표 라벨만 monospace. 원본 폰트 미사용 |
| 버튼/그래픽 | 밝은 직사각형 시작 버튼과 어두운 테두리. 일반 카드 대신 장면 중심 | 네이티브 버튼 개념 노드, 테두리·독자적 입체 바닥·큰 CTA |
| 움직임 | FLOAT 4700/4800/5100/5200ms, SWIRL 5000ms | 5000ms/6px 부유·멈춤 제어. 읽기/입력 영역 고정 |
| 스크롤 | 초기 desktop 높이=960px, wheel 후 scrollY=0 | 기능 안내는 정상 스크롤. 스크롤 가로채기 없음 |
| 이동/메뉴 | 초기 시작 링크·쿠키 설정/거부 확인. 거부 후 시작 클릭도 시도했으나 본편 전환은 확인 못함 | Router 이동·네이티브 dialog·모바일 disclosure. 미확인 본편을 추측해 재현하지 않음 |
| 입력 피드백 | 첫 화면 버튼만 확인. 본편 입력/선택과 정확한 hover 속도는 미확인 | 독자적 140ms press/hover, 선택 테두리/aria-pressed, 요청 로딩/오류 |
| 모바일 | 로고/배경 축소, 옆 섬 일부 잘림. 쿠키 패널 세로 적층 | 모든 개념 노드를 화면 안에 유지, 메뉴·단일 열 폼 |
| 특징 | 픽셀 아트·우주·부유 섬·게임 진입 장면 | 원본 섬/인물 대신 직접 만든 CSS/SVG 회로·문자·궤도 |

원본 게임 전체·모든 메뉴/모바일 화면·최종 미션·정확한 클릭 전환 시간은 검증하지 않았다. 관찰한 애니메이션 주기를 모든 인터랙션의 속도로 일반화하지 않는다. 증거는 Git 제외 reports/ui-qa/reference-*.png 및 reference-analysis.json에 보관했다. 실제 화면을 먼저 확인한 뒤 구현했다.

## 디자인 시스템

[tokens.css](../../frontend/src/shared/styles/tokens.css)와 [공통 스타일](../../frontend/src/shared/styles/global.css)로 관리한다. 페이지별 CSS 복제는 없으며 지도 좌표/기하는 일러스트레이션 위치와 구분한다.

| 항목 | 선택 |
|---|---|
| Color | bg #0d131b, panel #151e29, ink #f0f1eb, muted #b1bac5, accent #d6f599, error #ffb8ae |
| Typography | Pretendard Variable 로컬 제공. 본문 15px/1.7, 보조 13px, 제목 20/28px, 큰 제목 fluid 42~70px. 기술 라벨·코드는 mono |
| Spacing | 4/8/12/16/24/32/48/64/96px, fluid page gutter |
| Border/Radius | 1px line, 6/14/24px, pill. 상태는 글자/속성도 함께 제공 |
| Shadow/Depth | 패널 그림자·glyph 입체 바닥. 폼은 고정 |
| Buttons | primary 연두, secondary 테두리, quiet 텍스트. 최소 높이 48px, busy 중 중복 제출 방지 |
| Input | label/autocomplete/describedby 오류, 비밀번호 보기, 서버와 같은 문자·바이트 검증 |
| Cards | 인증·개념 설명·실제 계정 패널. 가짜 학습 통계 없음 |
| Navigation | Router·skip link·이동 후 main focus·모바일 Escape/focus 복귀 |
| Animation | press/hover 140ms, 선택 220ms, 페이지 260ms, 부유 5000ms. 대비 교정으로 텍스트 전체 fade 제거 |
| Breakpoints | 980px tablet 보정, 680px 단일 열/모바일 메뉴. media query는 공통 CSS 하단에 집중. 320px까지 검사 |

`prefers-reduced-motion`에서 부유·회전·페이지 움직임·smooth scroll을 제거하고 지도 멈춤 버튼도 제공한다. 애니메이션이 입력을 막지 않는다. 사용자 요청으로 Pretendard Variable v1.3.9를 OFL과 함께 로컬 제공하며 런타임 폰트 CDN은 호출하지 않는다. 본문·버튼·입력은 공통 글꼴을 쓰고 코드·기술 라벨의 monospace는 유지한다. 모든 사용자 텍스트는 Vue 이스케이프 렌더링을 사용한다.

## 화면 범위와 후속 계획

저장소에 C08 프론트 구현은 없었다. 기존 API 계약을 그대로 연결하는 소개·가입·로그인·본인 계정을 추가했다. 계정은 학습 마이페이지가 아니다. 미구현 퀴즈/챗봇 버튼은 준비 중 안내만 표시하며 답변·채점·통계·랭킹을 만들지 않는다.

| 후속 화면 | 적용 계획 |
|---|---|
| 분야/퀴즈 목록 | 5개 개념 지도 색/라벨을 실제 필터와 연결. 로딩/빈 결과/오류 분리 |
| 문제/결과 | 단일 집중 패널·진행 표시·네이티브 radio·서버 채점. 정답 미노출·짧은 피드백·즉시 읽는 해설 |
| 코드 | 본문 16px, 코드 최소 14px mono/1.6. 코드 컨테이너 안에서만 가로 스크롤 |
| AI 대화 | 약 70ch 읽기 패널·긴 코드/표의 내부 스크롤. 문맥·검색 근거·안전한 출처 URL·위치 유지. 생성 중/근거 부족/오류 분리 |
| 마이페이지/오답 | 실제 API 값만 사용. 로딩과 0건 구분, accuracy=null은 “—”. 복습/해결 상태 글자/아이콘 병기 |

이 계획은 미구현 기능의 출시·회귀 통과를 뜻하지 않는다. 실제 구현 시 서버 소유권·API·상태 검사를 추가한다.

C30 적용: /me 통계 카드·분야별 meter·서버 커서 이력, /me/wrong-answers 상태 필터·재풀이, /me/attempts/:attemptId 당시 결과를 연결했다. 통계는 API 값만 표시하며 null과 0%, 빈 이력과 장애를 구분한다. 기존 색·간격·폰트 토큰을 사용하고 카드 그리드는 600px 아래 두 열, 기록은 세로 배치다. Chrome 390px overflow·WCAG AA 자동 검사와 응답 유실 후 reload/동일 키 재확인을 검사한다. /account는 계정·로그아웃 역할을 유지하며 나의 학습 링크를 제공한다.
