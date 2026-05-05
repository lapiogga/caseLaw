# 시각 자료 인덱스 (promo/images)

본 폴더의 이미지·GIF 는 README 또는 docs 의 시각 가이드에서 참조된다.

## 자동 생성 (Playwright, 갱신 가능)

`docs/promo/automation/capture_pages.py` 실행 결과:

| 파일 | 설명 | 출처 |
|---|---|---|
| `01-github-repo.png` | GitHub 레포 메인 페이지 (전체) | github.com/lapiogga/caseLaw |
| `02-github-release.png` | v0.8.0 Release 페이지 | releases/tag/v0.8.0 |
| `03-pypi-package.png` | PyPI 패키지 페이지 | pypi.org/project/caselaw-mcp |
| `04-bopjecheo-openapi.png` | 법제처 OPEN API 첫 화면 | open.law.go.kr |
| `05-oc-baalgup-guide.png` | OC 발급 가이드 (GitHub 렌더링) | docs/OC발급_가이드.md |
| `06-installer-zip-download.png` | Release 첨부 자산 영역 | releases/tag/v0.8.0 (Assets) |

## 사용자 수동 캡처 (해당 시 추가)

| 파일 (제안) | 캡처 대상 | 도구 |
|---|---|---|
| `07-install-demo.gif` | demo-install-flow.ps1 시연 (25초) | ScreenToGif |
| `08-smartscreen-warning.png` | Windows SmartScreen 경고창 | Windows + Shift + S |
| `09-claude-desktop-tools.png` | Claude Desktop 도구 목록 (44 tools) | 본인 캡처 |
| `10-ping-success.png` | "caselaw 로 ping 해줘" 응답 | 본인 캡처 |
| `11-precedent-search.gif` | 음주운전 양형 검색 흐름 | ScreenToGif |
| `12-citizen-triage.gif` | 일반인 분쟁 분류 흐름 | ScreenToGif |

## 마크다운에서 참조하는 법

상대경로:

```markdown
![GitHub 레포](docs/promo/images/01-github-repo.png)
```

GitHub URL:

```markdown
![GitHub 레포](https://github.com/lapiogga/caseLaw/blob/main/docs/promo/images/01-github-repo.png?raw=true)
```

## 갱신 절차 (v0.9.0 배포 시)

```powershell
cd docs\promo\automation
.\.venv-pw\Scripts\python.exe capture_pages.py
git add docs\promo\images
git commit -m "docs(promo): 자동 캡처 갱신 (v0.9.0)"
git push
```

수동 캡처 자료(07~12)는 변경된 화면만 다시 캡처.
