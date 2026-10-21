# 외부 관리자의 필수 집행

- 실행 이미지는 digest로 고정하고 non-root·cap_drop·no-new-privileges·리소스 제한을 적용한다.
- /workspace는 비밀정보 없는 후보 복사본이다. 호스트 홈, SSH, Docker 소켓을 마운트하지 않는다.
- 도구 요청은 문자열 shell이 아닌 argv와 canonical path로 검사한다. symlink와 .. 우회를 차단한다.
- npm/Gradle/Python은 임의 코드를 실행할 수 있다. 명령 allowlist만 신뢰하지 않고 격리한다.
- 보호 파일 변경은 기준 SHA 대비 staged/unstaged/untracked 파일을 모두 검사한다.
- 검증은 후보와 분리한 신뢰된 정책/검증기로 수행한다. task는 acceptance criteria까지 독립 확인한다.
- 수집·모델 호출 브로커는 허용 목적지/경로·DNS 결과·리다이렉트를 매번 검사한다.
- localhost, 사설 IPv4/IPv6, link-local, metadata 주소 및 DNS rebinding을 차단한다.
- 키는 브로커에만 보관한다. 임의 요청 body 전달도 제한하고 모델명·토큰·동시성·비용 상한을 강제한다.
- GitHub 게시 자격증명은 실행 컨테이너에 전달하지 않는다. 읽기와 쓰기를 분리하고 task 범위를 검사한다.
- DB 테스트는 별도 내부 네트워크와 전용 DB/계정을 사용한다. 초기화도 해당 DB에만 허용한다.
- SIGKILL/호스트 장애 대비 상태 볼륨과 workspace snapshot을 관리자 권한으로 보존한다.

이 파일은 구현 체크리스트이며 현재 저장소에 외부 관리자·브로커는 구현되어 있지 않다.
