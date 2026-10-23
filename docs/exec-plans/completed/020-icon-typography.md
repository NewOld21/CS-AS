# 020 알고리즘 아이콘과 글꼴

Status: complete

사용자 요청: 알고리즘 노드의 중괄호를 네모 내부에 배치하고 전체 UI 글꼴을 개선한다. 범위는 frontend의 지도 glyph·공통 typography·로컬 font 자산과 문서다. 기존 PDF 입력과 019 미완료 사항은 보존한다.

원인: `{ }` 공백에서 줄바꿈될 수 있고 nowrap이 모바일에만 있었다. `{}`·공통 nowrap·중앙 정렬·크기 조정으로 교정한다. Pretendard Variable v1.3.9 원본과 OFL을 앱에서 직접 제공하고 본문/컨트롤에 공통 적용한다. 코드/기술 라벨은 기존 monospace를 유지한다.

검증: frontend build/lint/format, 실제 Chrome의 글꼴 로딩·320/390/768/1440px 중괄호 경계·overflow 및 기존 UI 회귀를 실행하고 결과를 기록한다.

2026-10-23: production build/typecheck·lint·format 통과. Chrome ui.spec.ts 8개(접근성 포함) 통과. 실제 document.fonts 로딩과 CSS family를 확인하고 네 너비에서 텍스트 Range 경계가 glyph frame 내부임을 검사했다. 모든 너비에서 가로 overflow 없음. reports/ui-qa/typography-check.json과 algorithm-390/1440.png, typography-390/1440.png로 증거를 남겼고 캡처를 시각 확인했다. Docker frontend 재시작·health 확인 후 사용자 접속 주소에 반영했다. 런타임 외부 폰트 요청은 없다.

첫 UI 회귀에서 근거 패널을 닫은 직후 늦게 끝난 페이지 전환이 버튼 focus를 main으로 가져가는 경합을 발견했다. 전환 완료 시 main 내부 요소에 이미 focus가 있으면 유지하도록 보정했다. Docker 재시작 후 최종 UI 8개를 다시 통과했으며 근거 패널의 키보드 focus 복귀 기준은 유지했다. Linux candidate 공통 검사도 355개 문서 링크·설정·하네스 19개를 통과했다.
