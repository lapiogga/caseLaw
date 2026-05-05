# =============================================================
# 설치 흐름 시연 스크립트 (실제 설치 안 함)
#
# 본 스크립트는 setup-for-novice.ps1 의 화면 출력을 그대로 재현하지만
# 실제 winget 설치·config 작성은 하지 않는다. 화면 녹화용.
#
# 사용:
#   ScreenToGif (https://www.screentogif.com) 또는 OBS Studio 실행
#   -> 녹화 영역을 PowerShell 창 크기로 지정
#   -> 본 스크립트 실행 (powershell -ExecutionPolicy Bypass -File demo-install-flow.ps1)
#   -> 녹화 멈춤 -> GIF 또는 MP4 저장
#
# 자동 시연 모드:
#   매 단계가 자동으로 진행되어 사용자 입력 대기 없음 (총 약 25초)
# =============================================================

$ErrorActionPreference = 'Stop'
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

function Write-Step { param($m); Write-Host ''; Write-Host '--------------------------------------------------------' -ForegroundColor Cyan; Write-Host "  $m" -ForegroundColor Cyan; Write-Host '--------------------------------------------------------' -ForegroundColor Cyan }
function Write-Ok   { param($m); Write-Host "  [OK] $m" -ForegroundColor Green }
function Write-Warn { param($m); Write-Host "  [!]  $m" -ForegroundColor Yellow }

function Demo-Pause { param([int]$Ms = 600); Start-Sleep -Milliseconds $Ms }
function Demo-Type {
    param([string]$Text, [int]$DelayMs = 35)
    foreach ($ch in $Text.ToCharArray()) {
        Write-Host -NoNewline $ch
        Start-Sleep -Milliseconds $DelayMs
    }
}

# 0. 환영
Clear-Host
Write-Host ''
Write-Host '  ============================================================' -ForegroundColor Magenta
Write-Host '   CaseLaw MCP 자동 설치 도구 (한국 판례·법령 검색)' -ForegroundColor Magenta
Write-Host '  ============================================================' -ForegroundColor Magenta
Write-Host ''
Write-Host '   이 도구는 Claude Desktop 에서 한국 판례·법령을 자연어로'
Write-Host '   검색·인용·요약할 수 있게 해줍니다.'
Write-Host ''
Write-Host '   소요 시간: 3-7분 (인터넷 속도에 따라)'
Write-Host ''
Write-Host -NoNewline '   계속하려면 Enter 를 누르세요: '
Demo-Pause 1500
Write-Host ''

# 1. OC 키
Write-Step '1단계: 법제처 OC 키 확인'
Write-Host ''
Write-Host '   OC 키는 법제처 OPEN API 사이트에서 무료로 발급받습니다.'
Write-Host ''
Write-Host -NoNewline '   이미 OC 키가 있습니까? (Y/N): '
Demo-Pause 1000
Demo-Type 'Y'
Write-Host ''
Write-Host ''
Write-Host -NoNewline '   OC 키를 붙여넣으세요: '
Demo-Pause 800
Demo-Type 'gildong' 60
Write-Host ''
Write-Ok 'OC 키 등록: gil*****'

# 2. 도구 점검
Write-Step '2단계: 필수 도구 점검 및 자동 설치'
Demo-Pause 400
Write-Ok 'winget 사용 가능'
Demo-Pause 400
Write-Host ''
Write-Host '   uv (Python 도구) 가 없습니다. 자동 설치합니다 (1-2분)...'
Demo-Pause 800
Write-Host -NoNewline '   '
1..30 | ForEach-Object { Write-Host -NoNewline '#' -ForegroundColor DarkGray; Start-Sleep -Milliseconds 60 }
Write-Host ''
Write-Ok 'uv 설치 완료'
Demo-Pause 400
Write-Ok 'Claude Desktop 이미 설치됨'
Demo-Pause 300
Write-Ok 'Claude Desktop config 폴더: C:\Users\...\Roaming\Claude'

# 3. 패키지
Write-Step '3단계: caselaw-mcp 패키지 다운로드 (PyPI)'
Demo-Pause 400
Write-Host '   uvx 로 caselaw-mcp 미리 받습니다 (30-60초)...'
Demo-Pause 600
Write-Host -NoNewline '   '
1..20 | ForEach-Object { Write-Host -NoNewline '#' -ForegroundColor DarkGray; Start-Sleep -Milliseconds 60 }
Write-Host ''
Write-Ok 'caselaw-mcp 설치 완료'

# 4. config
Write-Step '4단계: Claude Desktop 설정 자동 작성'
Demo-Pause 400
Write-Ok '기존 설정 백업: claude_desktop_config.json.backup-20260505-153012'
Demo-Pause 300
Write-Ok '설정 파일 작성 완료'

# 5. 완료
Write-Step '5단계: 설치 완료'
Write-Host ''
Write-Host '   모든 설정이 끝났습니다!' -ForegroundColor Green
Write-Host ''
Write-Host '   다음 절차로 사용하세요:'
Write-Host ''
Write-Host '   1) 트레이의 Claude Desktop 아이콘 -> Quit'
Write-Host '   2) 시작 메뉴에서 Claude Desktop 다시 실행'
Write-Host '   3) 채팅창에 입력해보세요:'
Write-Host ''
Write-Host '         caselaw 로 ping 해줘' -ForegroundColor Yellow
Write-Host ''
Write-Host '   문제 발생 시: https://github.com/lapiogga/caseLaw/issues'
Write-Host ''
Demo-Pause 2500
