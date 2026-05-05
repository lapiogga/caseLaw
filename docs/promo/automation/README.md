# 자동화 도구 (promo/automation)

본 폴더의 스크립트를 사용하면 홍보 자료(스크린샷·GIF) 의 상당 부분을 자동 생성할 수 있다. 향후 v0.9.0 등 업데이트 시 재실행만으로 자료 갱신 가능.

## 두 가지 자동화

| 도구 | 역할 | 자동화 수준 |
|---|---|---|
| `capture_pages.py` | 공개 웹 페이지 6장 PNG 캡처 (Playwright) | **완전 자동** |
| `demo-install-flow.ps1` | 설치 흐름 시연 (실제 설치 X, 화면 출력만 시뮬레이션) | **반자동** (녹화는 사용자가 ScreenToGif 로) |

자동화 불가능 (사용자 본인 PC 에서 수동 캡처 필요):
- Claude Desktop 채팅 화면 (Anthropic 계정 로그인)
- 법제처 회원가입·활용신청 화면 (캡차·이메일 인증)
- Windows SmartScreen 경고창

---

## 1. 공개 페이지 자동 캡처 (capture_pages.py)

### 무엇을 캡처하나?

| Slug | URL | 용도 |
|---|---|---|
| `01-github-repo` | github.com/lapiogga/caseLaw | 메인 페이지 |
| `02-github-release` | releases/tag/v0.8.0 | Release 첨부 자산 안내 |
| `03-pypi-package` | pypi.org/project/caselaw-mcp | PyPI 페이지 |
| `04-bopjecheo-openapi` | open.law.go.kr 첫 화면 | OC 발급 진입점 |
| `05-oc-baalgup-guide` | docs/OC발급_가이드.md (렌더링) | 가이드 자체 |
| `06-installer-zip-download` | Release ZIP 다운로드 위치 | 다운로드 흐름 |

### 실행 방법 (Windows)

```powershell
cd docs\promo\automation

# 1. 격리 venv 생성 (한 번만)
uv venv .venv-pw
uv pip install --python .\.venv-pw\Scripts\python.exe playwright

# 2. Chromium 다운로드 (한 번만, 약 200MB)
.\.venv-pw\Scripts\python.exe -m playwright install chromium

# 3. 캡처 실행 (매번)
.\.venv-pw\Scripts\python.exe capture_pages.py
```

결과는 `docs/promo/images/` 에 PNG 6장. 약 20-30초 소요.

### 새 페이지 추가

`capture_pages.py` 의 `PAGES` 리스트에 튜플 추가:

```python
("07-new-page", "https://example.com", 1280, 800, True, "css.selector"),
```

- 5번째 인자 `full_page=True` 면 전체 페이지 (긴 README 등), `False` 면 viewport 한 화면만
- 6번째 인자는 캡처 전 대기할 CSS selector (lazy-load 방지)

---

## 2. 설치 흐름 시연 (demo-install-flow.ps1)

### 무엇이 자동인가?

`setup-for-novice.ps1` 의 진짜 인터랙티브 입력(`Read-Host`) 부분을 모두 자동으로 진행한다 — 사용자 키보드 입력 없이 처음부터 끝까지 약 25초 안에 완주.

진짜 설치는 하지 않고 화면 출력만 시뮬레이션하므로 시스템에 영향 없다.

### 실행 방법

#### 옵션 A — ScreenToGif 로 GIF 만들기 (권장)

1. <https://www.screentogif.com> 에서 ScreenToGif 다운로드·실행
2. '레코더' 모드 선택
3. PowerShell 창을 열고, 녹화 영역을 PowerShell 창 크기로 지정
4. ScreenToGif 녹화 시작
5. PowerShell 에서 본 스크립트 실행:
   ```powershell
   powershell -ExecutionPolicy Bypass -File docs\promo\automation\demo-install-flow.ps1
   ```
6. 시연 종료 후 ScreenToGif 녹화 멈춤 → '편집' → 불필요한 프레임 잘라내기 → '저장' → GIF
7. 결과를 `docs/promo/images/07-install-demo.gif` 로 저장

#### 옵션 B — OBS Studio 로 MP4

1. OBS 의 '윈도우 캡처' 소스로 PowerShell 창 추가
2. 녹화 시작 → 본 스크립트 실행 → 녹화 멈춤
3. MP4 결과를 FFmpeg 로 GIF 변환:
   ```powershell
   ffmpeg -i input.mp4 -vf "fps=10,scale=720:-1:flags=lanczos" -loop 0 install-demo.gif
   ```

### 자동 녹화도 가능 (사용자 PC 에서, 본 환경 X)

PowerShell 의 Add-Type 으로 화면 캡처를 직접 코드로 할 수 있지만, 의존성·복잡도가 ScreenToGif 가 훨씬 낮으므로 추천하지 않는다.

---

## 3. 추천 워크플로 (총 30-40분)

```
1. capture_pages.py 실행 (자동)            -> images/01~06.png 생성
2. ScreenToGif 로 demo-install-flow 녹화    -> images/07-install-demo.gif
3. 본인 PC 에서 직접 캡처:
   - Claude Desktop 첫 채팅 결과 (ping)     -> images/08-ping-result.png
   - 실제 사용 예시 (음주운전 검색)          -> images/09-precedent-search.gif
4. images/README.md 의 인덱스에 새 자료 추가
5. 변경사항 commit + push
```

---

## 4. 정기 갱신 (v0.9.0 등 새 버전 배포 시)

GitHub Release 버전 번호가 바뀌면 `capture_pages.py` 의 PAGES 리스트의 `releases/tag/v0.8.0` 부분만 새 버전으로 변경 후 재실행.

PyPI 캡처는 자동으로 최신 버전을 보여주므로 수정 불필요.

---

## 5. 트러블슈팅

| 증상 | 원인 / 해결 |
|---|---|
| `playwright install` 200MB 다운로드 너무 느림 | 한 번만 받으면 됨. 또는 `playwright install --with-deps chromium` 으로 시스템 deps 도 자동 |
| 캡처에 한글이 깨짐 | viewport `locale="ko-KR"` 가 이미 설정됨. 그래도 깨지면 시스템 한글 폰트 확인 |
| 일부 페이지가 빈 화면 | networkidle 타임아웃. `capture_pages.py` 가 자동으로 domcontentloaded 로 fallback |
| Playwright 가 차단됨 (403) | User-Agent 추가 필요. `ctx = await pw.chromium.launch(... user_agent="Mozilla/5.0 ...")` |

---

## 격리 환경

본 폴더 안에서 만드는 `.venv-pw/` 는 .gitignore 로 추적 제외됨. 본 레포의 메인 `pyproject.toml` 의존성과 분리.
