# INSTALL — Gemini CLI 등록

> **대상**: Google 공식 [Gemini CLI](https://github.com/google-gemini/gemini-cli) 사용자
> **전제**: Gemini CLI v0.2 이상 설치 + `caselaw-mcp` 설치 완료(아래 1.A 또는 1.B)
> **예상 시간**: 5 분

Gemini CLI 는 로컬 stdio MCP 를 그대로 지원하므로 **추가 코드 변경 없이** Claude Desktop 과 동일한 stdio 진입점을 사용한다.

---

## 1. caselaw-mcp 설치

### A. PyPI (권장)

```powershell
# uv 설치 (1회)
irm https://astral.sh/uv/install.ps1 | iex
# 매번 실행 시 자동 격리 환경에서 호출
uvx caselaw-mcp --help
```

`uvx` 가 매 실행마다 격리 venv 를 만들어 caselaw-mcp 를 띄운다. 별도 install 불필요.

### B. 로컬 클론(개발자)

```powershell
cd C:\Users\User
git clone https://github.com/lapiogga/caseLaw.git CaseLaw
cd CaseLaw
uv sync
```

### C. OC 키 설정

법제처 OPEN API 인증 ID(OC)를 발급받고(`docs/OC발급_가이드.md` 참조) `.env` 또는 환경변수에 저장:

```powershell
# 프로젝트 디렉토리 루트에 .env
"CASELAW_OC=본인_ID" | Out-File -Encoding utf8 .env
```

---

## 2. Gemini CLI 등록 — 옵션 A: 명령어로 추가 (가장 빠름)

### A-1. uvx 방식 (PyPI 설치)

```powershell
gemini mcp add caselaw `
  --scope user `
  -- uvx caselaw-mcp
```

### A-2. uv run 방식 (로컬 클론)

```powershell
gemini mcp add caselaw `
  --scope user `
  -e CASELAW_OC=본인_ID `
  -- uv run --directory C:\Users\User\CaseLaw caselaw-mcp
```

`--scope user` 는 `~/.gemini/settings.json` 의 사용자 전역 영역에 저장. 프로젝트 한정은 `--scope project`.

---

## 3. Gemini CLI 등록 — 옵션 B: settings.json 직접 편집

### B-1. 파일 위치

| OS | 경로 |
|---|---|
| Windows | `%USERPROFILE%\.gemini\settings.json` |
| macOS / Linux | `~/.gemini/settings.json` |

### B-2. 구조

```json
{
  "mcpServers": {
    "caselaw": {
      "command": "uvx",
      "args": ["caselaw-mcp"],
      "trust": false,
      "timeout": 30000
    }
  }
}
```

uv 로컬 클론 변형:

```json
{
  "mcpServers": {
    "caselaw": {
      "command": "uv",
      "args": ["run", "--directory", "C:\\Users\\User\\CaseLaw", "caselaw-mcp"],
      "env": {
        "CASELAW_OC": "본인_ID"
      },
      "cwd": "C:\\Users\\User\\CaseLaw"
    }
  }
}
```

### B-3. 필드 의미

| 필드 | 설명 |
|---|---|
| `command` | 실행할 바이너리 (PATH 또는 절대경로) |
| `args` | 인자 배열 |
| `env` | 환경변수 (`$VAR_NAME` 으로 외부 환경변수 참조 가능) |
| `cwd` | 작업 디렉토리 (`.env` 자동 로드 대상) |
| `timeout` | 요청 타임아웃 ms |
| `trust` | true 면 도구 호출 시 확인 프롬프트 생략 (사용자 자가 책임) |

---

## 4. 검증

```powershell
# 등록 목록
gemini mcp list

# 출력 예시:
# caselaw  uvx caselaw-mcp  user
```

세션 시작 후 자연어로 호출:

```text
> caselaw 의 ping 도구 호출해 줘
```

또는 변호사 시나리오:

```text
> 음주운전 관련 최근 대법원 판례 5건의 사건번호와 선고일을 표로 정리해 줘.
```

Gemini CLI 가 자동으로 `caselaw.search_precedent` → `caselaw.get_precedent` 체이닝하여 응답한다.

---

## 5. 트러블슈팅

| 증상 | 원인 / 처리 |
|---|---|
| `gemini mcp list` 에 caselaw 안 보임 | settings.json 문법 오류 — JSON validator 로 확인 |
| 도구 호출 시 `oc_configured=false` | `.env` 또는 `env.CASELAW_OC` 누락 |
| `command not found: uvx` | `uv` 미설치. `irm https://astral.sh/uv/install.ps1 \| iex` 실행 후 새 PowerShell |
| 타임아웃 발생 | `timeout` 필드를 `60000` 등으로 증가. 첫 호출은 캐시 미스로 느림 |
| 도구가 모두 비활성 표시 | `trust: true` 설정 또는 매번 도구 호출 시 [Y]es 응답 |

---

## 6. Claude Desktop 과의 차이

| 항목 | Claude Desktop | Gemini CLI |
|---|---|---|
| Config 위치 | `%APPDATA%\Claude\claude_desktop_config.json` (또는 MSIX 격리 경로) | `~/.gemini/settings.json` |
| 등록 명령 | 수동 편집 또는 `scripts/install-caselaw-mcp.ps1` | `gemini mcp add` 또는 `scripts/install-caselaw-gemini.ps1` |
| 도구 신뢰 모델 | 매번 사용자 승인 UI | `trust` 필드로 일괄 신뢰 가능 |
| 호출 표면 | GUI 채팅 | 터미널 채팅 (`gemini` 세션) |
| 코드 변경 | 없음 | 없음 (동일한 stdio 엔트리포인트) |

---

## 7. 원클릭 등록 스크립트

`scripts/install-caselaw-gemini.ps1` 실행 시 위 설정을 자동 작성한다(미존재 settings.json 생성, 기존 파일은 백업 후 병합).

```powershell
cd C:\Users\User\CaseLaw
.\scripts\install-caselaw-gemini.ps1
```

본문 절차는 동일하므로 수동 편집을 선호하면 본 스크립트를 건너뛴다.
