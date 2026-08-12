# GitHub Pages 자동배포

이 프로젝트는 `main` 브랜치에 업로드하면 GitHub Actions가 Safari용 PWA를 GitHub Pages에 자동 배포하도록 구성되어 있습니다.

## 최초 1회 설정

1. GitHub에서 새 저장소를 만듭니다. 예: `metal-cbt`.
2. 이 폴더의 **내용 전체**를 저장소 최상단에 업로드합니다. `.github` 폴더도 반드시 포함해야 합니다.
3. 저장소의 **Settings → Pages**로 이동합니다.
4. **Build and deployment → Source**를 **GitHub Actions**로 선택합니다.
5. `main` 브랜치에 파일이 올라가면 **Actions** 탭에서 `Deploy CBT PWA to GitHub Pages`가 자동 실행됩니다.
6. 배포 성공 후 Pages 화면 또는 Actions 실행 결과에 표시된 HTTPS 주소로 접속합니다.

일반적인 프로젝트 저장소의 주소 형태는 다음과 같습니다.

`https://<GitHub아이디>.github.io/<저장소이름>/`

## iPad 설치

1. 위 HTTPS 주소를 iPad의 Safari에서 엽니다.
2. 페이지가 정상적으로 한 번 로드될 때까지 기다립니다.
3. Safari **공유** 버튼을 누릅니다.
4. **홈 화면에 추가**를 선택합니다.
5. 생성된 `금속 CBT` 아이콘으로 실행합니다.

Service Worker가 문제 데이터와 앱 파일을 캐시하므로 한 번 정상 로드된 뒤에는 오프라인에서도 사용할 수 있습니다. 학습기록, 오답, 별표, 메모와 복습 일정은 Safari의 IndexedDB에 저장됩니다.

## 업데이트

문제 또는 앱 코드를 수정해 `main`에 다시 업로드하면 GitHub Actions가 자동으로 새 버전을 배포합니다. PWA 캐시 버전을 강제로 바꾸고 싶을 때는 `sw.js`의 캐시 이름(`C`)을 변경하면 됩니다.

## 주의

Safari 데이터를 삭제하거나 해당 웹사이트 데이터를 제거하면 iPad에 저장된 학습기록도 삭제될 수 있습니다. 여러 기기 간 학습기록 동기화는 현재 버전에 포함되어 있지 않습니다.
