# 금속재료기사 CBT Pro v4 — Safari / iPad PWA

iPad Safari와 PC 브라우저에서 동일하게 사용할 수 있는 금속재료기사 CBT 학습 앱입니다.

## 주요 기능

- 검증 핵심 2,000문제
- 핵심문항당 동적 파생형을 생성하여 가상 50,000문제 제공
- 과목 / 세부영역 / 난이도별 학습
- 오답노트: 오답 등록 후 2회 연속 정답 시 해제
- 1·3·7·14·30·60·120일 간격복습
- 오늘 복습 / 취약문제 우선출제
- 별표 / 검토 표시 / 문제별 메모
- 실전 100문제: 5과목 × 20문제
- 150분 타이머
- 평균 60점 이상 + 과목별 40점 미만 과락 판정
- 문제번호 답안판
- IndexedDB 로컬 학습기록 저장
- Service Worker 오프라인 캐시
- iPad 가로·세로 반응형 UI

## GitHub Pages 배포

자동배포 workflow가 포함되어 있습니다.

1. 새 GitHub 저장소를 생성합니다.
2. 이 폴더의 내용 전체를 저장소 루트에 업로드합니다.
3. **Settings → Pages → Source → GitHub Actions**를 선택합니다.
4. `main` 브랜치에 push하면 `.github/workflows/deploy-pages.yml`이 자동으로 Pages 배포를 수행합니다.
5. 배포된 HTTPS 주소를 iPad Safari로 연 뒤 **공유 → 홈 화면에 추가**를 선택합니다.

자세한 순서는 `DEPLOY_GITHUB_PAGES.md`를 참고하세요.

## PC 로컬 테스트

Windows에서 `run_local.bat`을 실행하고 다음 주소를 엽니다.

`http://localhost:8000`

## 데이터 구조

`data/questions.json`에는 검증 핵심 2,000문제가 들어 있습니다. 파생형 48,000개는 브라우저에서 정답 선택지 매핑을 유지한 채 동적으로 구성되므로 50,000개 JSON을 직접 저장하지 않습니다.

> 파생문항은 48,000개의 완전히 독립적인 신규 개념 문제가 아니라 핵심 2,000문제의 문형·선택지 변형입니다.
