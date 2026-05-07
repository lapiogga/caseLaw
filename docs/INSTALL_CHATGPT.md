# INSTALL — ChatGPT (Apps SDK / Developer Mode 커넥터)

> **대상**: ChatGPT Plus/Pro/Team/Enterprise 사용자 + Developer Mode 또는 Apps SDK 활용 가능한 환경
> **전제**: caselaw-mcp 가 로컬에 설치되어 있고 OC 키 발급 완료
> **예상 시간**: 15 ~ 30 분 (Cloudflare 또는 ngrok 가입 포함 시)

ChatGPT 는 Claude Desktop·Gemini CLI 와 달리 **로컬 stdio MCP 를 직접 호출하지 않는다**. 대신 HTTPS 엔드포인트로 노출된 **Remote MCP** 만 받아들인다. 따라서 caselaw-mcp 를 다음 3 단계로 노출한다:

1. **HTTP 모드 boot** — `caselaw-mcp --transport http`
2. **HTTPS 외부 노출** — Cloudflare Tunnel(권장) 또는 ngrok
3. **ChatGPT 커넥터 등록** — Bearer 토큰으로 인증

---

## 0. 보안 경고 ⚠️

본 가이드는 caselaw-mcp 를 인터넷에 노출시킨다. 반드시:

- **Bearer 토큰 무작위 32 자 이상** 생성하여 `CASELAW_AUTH_TOKEN` 에 설정
- 토큰을 잃어버렸거나 노출된 정황이 있으면 즉시 회전
- OC 키는 별도(`CASELAW_OC`) 로컬에만 저장. 절대 ChatGPT 커넥터 설정에 직접 넣지 않는다(서버 측에서 `.env` 로 주입)
- 외부 노출 도구(터널)는 사용자 본인 계정으로만 운용

caselaw 데이터 자체는 공개 정보이지만, OC 키 호출 한도가 본인 한도이므로 토큰이 새면 도용 가능성이 있다.

---

## 1. caselaw-mcp HTTP 모드 boot

### 1-1. Bearer 토큰 발급

```powershell
# Windows PowerShell — 안전한 32바이트 무작위 토큰 생성
$bytes = New-Object byte[] 32
(New-Object System.Security.Cryptography.RNGCryptoServiceProvider).GetBytes($bytes)
$token = [Convert]::ToBase64String($bytes) -replace '[+/=]', ''
Write-Host "TOKEN: $token"
```

생성된 토큰을 `.env` 또는 환경변수로 저장:

```powershell
# 프로젝트 디렉토리의 .env 에 추가
Add-Content -Path .env -Value "CASELAW_AUTH_TOKEN=$token"
```

### 1-2. HTTP 모드 실행

```powershell
cd C:\Users\User\CaseLaw

# .env 자동 로드 (CASELAW_OC + CASELAW_AUTH_TOKEN)
uv run caselaw-mcp --transport http --host 127.0.0.1 --port 8000
```

성공 시:

```
INFO:     Started server process [...]
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

엔드포인트 = `http://127.0.0.1:8000/mcp` (말미 슬래시 자동 처리).

### 1-3. 로컬 검증

```powershell
$headers = @{ "Authorization" = "Bearer $env:CASELAW_AUTH_TOKEN"; "Content-Type" = "application/json"; "Accept" = "application/json, text/event-stream" }
$body = '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}'
Invoke-RestMethod -Uri "http://127.0.0.1:8000/mcp/" -Method POST -Headers $headers -Body $body
```

`serverInfo.name = "caselaw-mcp"` 가 회신되면 정상.

---

## 2. HTTPS 외부 노출 — 옵션 A: Cloudflare Tunnel (권장)

**장점**: 무료, 도메인 불필요(`*.trycloudflare.com` 자동), HTTPS 자동, 신용카드 불요.
**단점**: 임시 도메인은 매 실행마다 변경 (영구 도메인 필요 시 Named Tunnel + DNS 설정).

### 2-A-1. cloudflared 설치

```powershell
winget install --id Cloudflare.cloudflared
```

또는 [공식 다운로드 페이지](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/) 에서 `cloudflared.exe` 직접 받기.

### 2-A-2. 임시 터널 실행

```powershell
cloudflared tunnel --url http://localhost:8000
```

출력 예:

```
Your quick Tunnel has been created! Visit it at:
https://random-words-xxxx.trycloudflare.com
```

이 URL 이 ChatGPT 가 호출할 **퍼블릭 엔드포인트**. ChatGPT 커넥터에는 아래를 입력:

```
https://random-words-xxxx.trycloudflare.com/mcp
```

### 2-A-3. 영구 도메인 (선택)

자체 도메인을 Cloudflare 에 등록한 후 [Named Tunnel](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/get-started/create-remote-tunnel/) 패턴으로 운용. 본 문서 범위 외.

---

## 3. HTTPS 외부 노출 — 옵션 B: ngrok

**장점**: 익숙함, 인터페이스 단순.
**단점**: 무료 플랜은 임시 도메인 + 세션당 시간 제약 + ngrok 계정 가입 필요.

### 3-B-1. 설치 + 인증

```powershell
winget install --id Ngrok.Ngrok
ngrok config add-authtoken YOUR_NGROK_TOKEN
```

### 3-B-2. 터널 실행

```powershell
ngrok http 8000
```

출력의 `Forwarding` 행 (`https://xxxx-xxx-xx.ngrok-free.app`) 을 사용. ChatGPT 커넥터에는 `/mcp` 를 붙여 등록.

---

## 4. ChatGPT 커넥터 등록

ChatGPT 의 MCP 지원은 빠르게 진화 중이므로 UI 가 바뀔 수 있다. 2026 년 5 월 기준 절차:

### 4-1. Developer Mode 활성화

1. ChatGPT 좌하단 프로필 → **Settings**
2. **Connectors** (또는 **Apps & Connectors**) 메뉴
3. **Developer mode** 토글 ON

### 4-2. 신규 커넥터 추가

1. **+ Add connector** → **Custom MCP server**
2. 입력:

| 필드 | 값 |
|---|---|
| Name | `caselaw` |
| Description | 한국 법령·판례 검색 (법제처 OPEN API) |
| Server URL | `https://random-words-xxxx.trycloudflare.com/mcp` |
| Authentication | `Bearer token` |
| Token | (1-1 에서 생성한 `CASELAW_AUTH_TOKEN` 값) |

3. **Test connection** → 200 OK + 도구 목록 반환 확인 (44 종)
4. **Save**

### 4-3. 활성화 후 호출

새 채팅에서 `+` → **Connectors** → `caselaw` 활성. 자연어로:

```text
caselaw 로 음주운전 관련 최근 대법원 판례 5 건의 사건번호와 선고일을 표로.
```

---

## 5. Apps SDK 통합 (개발자 — 선택)

OpenAI Apps SDK 로 ChatGPT 안에 설치형 앱을 만들 때도 동일한 caselaw HTTPS 엔드포인트를 MCP 백엔드로 등록할 수 있다. 자세한 절차는 [OpenAI MCP 가이드](https://developers.openai.com/api/docs/mcp) 참조.

---

## 6. 트러블슈팅

| 증상 | 원인 / 처리 |
|---|---|
| Test connection → `401 unauthorized` | Bearer 토큰 불일치. `.env` 와 ChatGPT 커넥터 입력값 정확히 동일한지 확인 (앞뒤 공백·복붙 줄바꿈) |
| Test connection → `Connection refused` | 로컬 서버 다운. `caselaw-mcp --transport http` 재시작 |
| Test connection → `404` | URL 끝에 `/mcp` 누락. `https://.../mcp` 또는 `https://.../mcp/` 사용 |
| ChatGPT 가 도구 호출 안 함 | Developer mode OFF · 커넥터 비활성 · 새 채팅에서 다시 활성화 필요 |
| Cloudflare Tunnel 갑자기 종료 | 무료 임시 터널은 PC 절전·네트워크 변경에 취약. Named Tunnel 권장 |
| `oc_configured=false` 응답 | 서버 환경에 `CASELAW_OC` 누락. `.env` 확인 후 재기동 |

---

## 7. 운영 체크리스트

| | 항목 |
|---|---|
| ☐ | `CASELAW_AUTH_TOKEN` 32 자 이상 무작위 |
| ☐ | `.env` 파일 git ignore 확인 (`git check-ignore .env`) |
| ☐ | 토큰을 채팅·문서·이슈에 평문 노출 금지 |
| ☐ | 사용 종료 시 터널 종료 (Ctrl+C) — 24/7 노출 불필요 시 |
| ☐ | OC 사용량 주기적 확인 (법제처 마이페이지) |
| ☐ | 토큰 의심 시 즉시 회전 + 서버 재기동 |
