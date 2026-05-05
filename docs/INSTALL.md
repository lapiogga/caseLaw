# INSTALL — Claude Desktop / Cursor / VS Code 등록

> **전제**: Phase 0/1 완료 (의존성 동기화·OC 키 설정 끝).

## 1. Claude Desktop (Windows)

### 1.1 config 파일 위치

```
%APPDATA%\Claude\claude_desktop_config.json
```

PowerShell에서 바로 열기:

```powershell
notepad "$env:APPDATA\Claude\claude_desktop_config.json"
```

파일이 없으면 새로 만든다.

### 1.2 등록 (uv 사용 — 권장)

```json
{
  "mcpServers": {
    "caselaw": {
      "command": "C:\\Users\\User\\.local\\bin\\uv.exe",
      "args": [
        "run",
        "--directory",
        "C:\\Users\\User\\CaseLaw",
        "caselaw-mcp"
      ]
    }
  }
}
```

`OC` 키는 프로젝트 디렉토리의 `.env` 에서 자동 로드되므로 **config에 넣지 않는다** (시크릿이 config 파일에 평문 저장되는 것 방지).

### 1.3 환경변수로 OC 주입(대안 — `.env` 사용 안 할 때)

```json
{
  "mcpServers": {
    "caselaw": {
      "command": "C:\\Users\\User\\.local\\bin\\uv.exe",
      "args": ["run", "--directory", "C:\\Users\\User\\CaseLaw", "caselaw-mcp"],
      "env": {
        "CASELAW_OC": "본인_ID"
      }
    }
  }
}
```

### 1.4 적용 절차

1. config 저장
2. Claude Desktop **완전 종료** (트레이 아이콘에서 Quit)
3. 다시 실행
4. 채팅 입력창 좌하단 도구 아이콘 → `caselaw` 서버에 6개 tool 표시 확인
5. 첫 명령: **"caselaw로 ping 해봐"** → `{"status":"ok","oc_configured":true,"phase":"1-mvp"}` 반환되면 성공

### 1.5 트러블슈팅

| 증상 | 원인 / 해결 |
|---|---|
| 서버 목록에 caselaw 안 뜸 | config JSON 문법 오류. `python -m json.tool < config.json` 으로 검증 |
| `oc_configured: false` | `.env` 가 `--directory` 경로에 있는지, `CASELAW_OC=값` 형태 맞는지 확인 |
| `command not found: uv` | uv 절대경로 사용 (`C:\Users\User\.local\bin\uv.exe`) |
| 첫 호출 timeout | 30s 기본. `CASELAW_HTTP_TIMEOUT=60` 으로 늘림 |
| 한글 깨짐 | Claude Desktop은 UTF-8 정상. PowerShell 콘솔 출력만 cp949 영향 |

---

## 2. Cursor

`Settings` → `MCP` → `+ Add new MCP server` → 위 JSON 동일 형식 입력.
또는 `~/.cursor/mcp.json` 에 동일 구조로 추가.

---

## 3. VS Code (Cline / Continue 확장)

확장별 다르지만 대체로 `mcpServers` 키 동일 구조 지원.

---

## 4. 개발자 모드 (FastMCP Inspector)

코드 수정·디버깅에 유용:

```powershell
cd C:\Users\User\CaseLaw
uv run mcp dev src\caselaw_mcp\server.py
```

브라우저에서 도구 목록·실행·응답을 직접 확인.

---

## 5. 보안 체크리스트

- [ ] `.env` 파일이 `.gitignore` 에 포함됨 (이미 적용)
- [ ] `claude_desktop_config.json` 에 OC 평문 노출 안 함 (`.env` 권장)
- [ ] 캐시 DB(`~/.caselaw_mcp/cache.db`)는 사용자 홈에 한정 — 다른 사용자 접근 불가 권한 확인
- [ ] 로그에 `***OC***` 마스킹 적용됨 (자동)
