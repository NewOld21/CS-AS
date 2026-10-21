# 012 레퍼런스 분석 기반 Vue UI

Status: completed

## 목표·범위

레퍼런스를 실제 Chrome으로 먼저 확인한 뒤 CS/AS의 독자적 학습 공간을 구현한다. allowed_paths: frontend/, scripts/, docs/. backend API·DB·인증 정책·RAG·하네스 정책은 변경하지 않는다. 시작 커밋 ee14ca7, git status clean. 현재 frontend에는 README/AGENTS만 있으며 C08 화면·Router·상태·API Client가 없다. 기존 인증 계약을 지키는 Vue 기반 소개/인증/본인 계정 화면을 추가한다. 퀴즈·챗봇·학습 마이페이지는 미구현이므로 디자인 계획만 남기고 가짜 서비스/통계를 표시하지 않는다.

## 순서·완료 조건

- [x] 실제 레퍼런스 desktop/mobile/시작/스크롤 관찰과 미확인 범위 기록.
- [x] 디자인 토큰·공통 컴포넌트·랜딩·로그인/가입·본인 계정 구현.
- [x] 기존 세션/CSRF API 연결과 오류·로딩·성공·만료 상태 검사.
- [x] 실제 브라우저 desktop/tablet/mobile, keyboard, reduced motion, 대비/접근성.
- [x] TypeScript·lint·단위/E2E·build·Linux 공통 검사, 실행/후속 계획 기록.

## Baseline·도구

웹 추출 도구는 레퍼런스 접근 실패. Chrome 1440x960와 390x844는 실제 HTTP 200/스크린샷 확인 성공. 원본 로고·이미지·소스·픽셀 그래픽은 제품에 사용하지 않는다. Node 24.18.0/npm 11.16.0. Sites 스킬은 기존 checkout의 로컬 디자인/QA 지침만 적용하며 호스팅/사이트 생성은 범위 밖이다. 브라우저 참조 증거는 reports/ui-qa/에 저장한다.

## 완료 증거 (2026-10-21)

실제 관찰/미확인 범위·시각 선택·토큰·학습 화면 계획은 [UI 시스템](../../design/ui-system.md)에 기록했다. Vue 소개·가입·로그인·계정, 공통 BrandMark/BaseButton/FormField/StatusMessage/OrbitMap/FeatureDialog, Router·Pinia·API client를 추가했다. backend/·Compose·공개 OpenAPI·DB·보안 정책·RAG 코드는 변경하지 않았다.

| 검사 | 실제 결과 |
|---|---|
| `python scripts/frontend.py check` | exit 0: Prettier·vue-tsc·ESLint·Vitest 8 tests·Vite build PASS |
| `CSAS_E2E_API=http://localhost:18080 npm run test:e2e` | exit 0, 8 tests PASS, skip 없음. UI 오류 fixture와 실제 인증 API test를 분리 |
| 실제 API 흐름 | 전용 PostgreSQL 앱: 가입 201·중복 409·잘못된 로그인 401·정상 로그인·본인 계정·새로고침 세션 복원·모바일 로그아웃·재접근 로그인 이동 PASS |
| 반응형 | Chrome 1440/768/390/320px 소개/로그인/가입 가로 넘침 없음. 본인 계정 desktop/mobile도 확인 |
| 키보드/상태 | 지도 Enter/선택 상태·dialog Escape/포커스 복귀·모바일 메뉴 Escape·오류 첫 필드 focus·로딩 중 중복 제출 방지 PASS |
| 접근성 | 소개/로그인/가입 axe WCAG 2/2.1 A/AA 위반 0, Reduced Motion에서 animation-name=none, 사용자 멈춤 버튼 PASS |
| Linux 공통 검사 | Python 3.12.10 source-only snapshot의 `python3 scripts/verify.py`: exit 0, 문서/하네스 구조·회귀 19 tests PASS |
| 변경 범위/비밀정보 | 실제 .env와 node_modules·reports는 Git 제외. backend/·Compose·OpenAPI diff 없음. 사용자 데이터/자격증명 삭제·노출 없음 |

실제 화면을 시각 검토한 증거는 reports/ui-qa/의 landing-desktop/mobile/tablet, login-desktop, signup-mobile, account-desktop/mobile PNG다. 원본 사이트 자료도 같은 Git 제외 위치에만 보관하며 제품 자산으로 포함하지 않았다. 최초 프론트 검사 실패는 접근성 도구의 Playwright 타입 중복을 고정 override로 교정했고, 최초 E2E 실패의 320px 지도 비율 넘침과 페이지 fade 중 대비를 width 고정/텍스트 fade 제거로 교정했다. 검사 기준을 완화하거나 실패 항목을 제외하지 않았다.

## 미확인·인계

원본 본편 게임 전환·전체 메뉴/입력/최종 미션·모든 모바일 상태는 미확인이다. 구현 UI는 실제 Chrome에서 확인했으며 Safari/Firefox·실물 모바일·스크린리더 사용자 검토는 수행하지 않았다. axe는 접근성 전체 보증이 아니다. 아직 존재하지 않는 퀴즈·챗봇·학습 통계의 기능 회귀는 실행 대상이 없으며 준비 중 안내와 후속 계획만 제공했다. 다음은 기존 002/004/005 범위의 실제 학습 기능/내부 RAG 연동이다. 실행은 [개발 안내](../../development.md)를 따른다.
