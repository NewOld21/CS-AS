# Frontend

Vue 3.5.22 + TypeScript 5.9.3 + Router 4.6.3 + Pinia 3.0.3. Node 22.12+와 npm을 사용한다. `npm ci` 후 루트에서 `python scripts/frontend.py dev`로 실행한다. `python scripts/frontend.py check`는 포맷·타입·lint·8개 단위 검사·빌드를 수행한다. 실제 Chrome E2E는 `python scripts/frontend.py e2e`다. 자세한 API 연결·전용 DB 검증은 [개발 안내](../docs/development.md), 디자인과 미구현 학습 화면 계획은 [UI 시스템](../docs/design/ui-system.md)을 따른다.

[작업 안내](AGENTS.md)를 읽는다. Vue/TypeScript는 src/app, src/domains, src/shared에서 구현한다.
랜딩·가입·로그인·본인 계정을 제공한다. 퀴즈·챗봇·학습 마이페이지는 후속이며 현재 구현 범위와 구분한다.
