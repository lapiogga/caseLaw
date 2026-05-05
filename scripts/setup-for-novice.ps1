# =============================================================
# CaseLaw MCP 비기술자용 자동 설치 스크립트
# .bat 파일이 호출. 직접 실행은 권장하지 않음.
# =============================================================

$ErrorActionPreference = 'Stop'
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

function Write-Step {
    param([string]$Message)
    Write-Host ''
    Write-Host '--------------------------------------------------------' -ForegroundColor Cyan
    Write-Host "  $Message" -ForegroundColor Cyan
    Write-Host '--------------------------------------------------------' -ForegroundColor Cyan
}

function Write-Ok {
    param([string]$Message)
    Write-Host "  [OK] $Message" -ForegroundColor Green
}

function Write-Warn {
    param([string]$Message)
    Write-Host "  [!]  $Message" -ForegroundColor Yellow
}

function Write-Err {
    param([string]$Message)
    Write-Host "  [X]  $Message" -ForegroundColor Red
}

function Test-Command {
    param([string]$Name)
    return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}

# ─────────────────────────────────────────────
# 0. 환영 메시지
# ─────────────────────────────────────────────
Clear-Host
Write-Host ''
Write-Host '  ============================================================' -ForegroundColor Magenta
Write-Host '   CaseLaw MCP 자동 설치 도구 (한국 판례·법령 검색)' -ForegroundColor Magenta
Write-Host '  ============================================================' -ForegroundColor Magenta
Write-Host ''
Write-Host '   이 도구는 Claude Desktop 에서 한국 판례·법령을 자연어로'
Write-Host '   검색·인용·요약할 수 있게 해줍니다.'
Write-Host ''
Write-Host '   설치 진행 전 다음을 확인합니다:'
Write-Host '     1. 법제처 OC 키 (무료, 본인이 직접 발급해야 함)'
Write-Host '     2. Python / uv / Claude Desktop (없으면 자동 설치)'
Write-Host ''
Write-Host '   소요 시간: 3-7분 (인터넷 속도에 따라)'
Write-Host ''
Read-Host '   계속하려면 Enter 를 누르세요'

# ─────────────────────────────────────────────
# 1. OC 키 입력 (또는 발급 가이드 열기)
# ─────────────────────────────────────────────
Write-Step '1단계: 법제처 OC 키 확인'

Write-Host ''
Write-Host '   OC 키는 법제처 OPEN API 사이트에서 무료로 발급받습니다.'
Write-Host '   (보통 가입 시 입력한 이메일 ID 의 @ 앞부분과 동일)'
Write-Host ''
$haveKey = Read-Host '   이미 OC 키가 있습니까? (Y/N)'

if ($haveKey -notmatch '^[Yy]') {
    Write-Host ''
    Write-Host '   브라우저로 다음 두 페이지를 자동으로 엽니다:'
    Write-Host '     - 발급 사이트 (회원가입 -> 활용신청)'
    Write-Host '     - 발급 가이드 (스크린샷 절차)'
    Write-Host ''
    Read-Host '   준비되면 Enter (브라우저 열림)'
    Start-Process 'https://open.law.go.kr/LSO/openApi/cuAskList.do'
    Start-Process 'https://github.com/lapiogga/caseLaw/blob/main/docs/OC%EB%B0%9C%EA%B8%89_%EA%B0%80%EC%9D%B4%EB%93%9C.md'
    Write-Host ''
    Write-Host '   발급이 끝나면 키를 복사한 후 본 창으로 돌아오세요.'
    Read-Host '   복사 완료 시 Enter'
}

$ocKey = ''
while ([string]::IsNullOrWhiteSpace($ocKey)) {
    $ocKey = Read-Host '   OC 키를 붙여넣으세요'
    if ([string]::IsNullOrWhiteSpace($ocKey)) {
        Write-Warn '키가 비어있습니다. 다시 입력해주세요.'
    }
}
$ocKey = $ocKey.Trim()
Write-Ok "OC 키 등록: $($ocKey.Substring(0, [Math]::Min(3, $ocKey.Length)))*****"

# ─────────────────────────────────────────────
# 2. 필수 도구 점검 + 자동 설치
# ─────────────────────────────────────────────
Write-Step '2단계: 필수 도구 점검 및 자동 설치'

# 2-1. winget
if (-not (Test-Command 'winget')) {
    Write-Err 'winget (Windows 패키지 관리자) 가 없습니다.'
    Write-Host '   Windows 10 1809+ / Windows 11 에서 기본 제공됩니다.'
    Write-Host '   Microsoft Store 에서 "App Installer" 를 설치하세요:'
    Write-Host '   https://www.microsoft.com/store/productid/9NBLGGH4NNS1'
    Read-Host '   설치 후 본 스크립트 다시 실행. Enter 로 종료'
    exit 1
}
Write-Ok 'winget 사용 가능'

# 2-2. uv (Python 도구)
if (-not (Test-Command 'uv')) {
    Write-Host ''
    Write-Host '   uv (Python 도구) 가 없습니다. 자동 설치합니다 (1-2분)...'
    $prevEAP = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
    $uvInstallOk = $false
    try {
        winget install --id astral-sh.uv --silent --accept-package-agreements --accept-source-agreements 2>&1 | Out-Null
        $env:Path = [System.Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' + [System.Environment]::GetEnvironmentVariable('Path', 'User')
        if (Test-Command 'uv') { $uvInstallOk = $true }
    } catch {
        Write-Warn "winget 호출 중 메시지: $($_.Exception.Message)"
    }
    $ErrorActionPreference = $prevEAP
    if ($uvInstallOk) {
        Write-Ok 'uv 설치 완료'
    } else {
        Write-Err 'uv 자동 설치에 실패했습니다.'
        Write-Host '   수동 설치: https://astral.sh/uv/install.ps1'
        Read-Host '   Enter 로 종료'
        exit 1
    }
} else {
    Write-Ok 'uv 이미 설치됨'
}

# 2-3. Claude Desktop
$claudeMsixDir = Join-Path $env:LOCALAPPDATA 'Packages\Claude_pzs8sxrjxfjjc'
$claudeAppDataDir = Join-Path $env:APPDATA 'Claude'

if ((Test-Path $claudeMsixDir) -or (Test-Path $claudeAppDataDir)) {
    Write-Ok 'Claude Desktop 이미 설치됨'
} else {
    Write-Host ''
    Write-Host '   Claude Desktop 이 없습니다.'
    Write-Host '   자동 설치를 시도합니다 (winget)...'
    $installed = $false
    $prevEAP = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
    try {
        winget install --id Anthropic.Claude --silent --accept-package-agreements --accept-source-agreements 2>&1 | Out-Null
        if ((Test-Path $claudeMsixDir) -or (Test-Path $claudeAppDataDir)) {
            $installed = $true
            Write-Ok 'Claude Desktop 설치 완료'
        }
    } catch {
        # winget 에 패키지 없으면 fallback
    }
    $ErrorActionPreference = $prevEAP
    if (-not $installed) {
        Write-Warn 'winget 자동 설치 실패. 브라우저로 다운로드 페이지를 엽니다.'
        Start-Process 'https://claude.ai/download'
        Read-Host '   Claude Desktop 설치 후 한 번 실행하고 본 창으로 돌아와 Enter'
    }
}

# Claude Desktop 을 한 번 실행해야 config 폴더가 생성됨
$configDirCandidates = @(
    (Join-Path $env:LOCALAPPDATA 'Packages\Claude_pzs8sxrjxfjjc\LocalCache\Roaming\Claude'),
    (Join-Path $env:APPDATA 'Claude')
)
$configDir = $configDirCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1

if (-not $configDir) {
    Write-Warn 'Claude Desktop config 폴더가 아직 없습니다. 한 번 실행한 후 종료해주세요.'
    Read-Host '   Claude Desktop 실행 -> 종료 후 Enter'
    $configDir = $configDirCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
}
if (-not $configDir) {
    Write-Err '여전히 config 폴더를 찾을 수 없습니다. 본 스크립트를 다시 실행해보세요.'
    Read-Host '   Enter 로 종료'
    exit 1
}
Write-Ok "Claude Desktop config 폴더: $configDir"

# ─────────────────────────────────────────────
# 3. PyPI 에서 caselaw-mcp 미리 다운로드 (uvx 첫 실행 속도 ↑)
# ─────────────────────────────────────────────
Write-Step '3단계: caselaw-mcp 패키지 다운로드 (PyPI)'

$uvPath = (Get-Command uv -ErrorAction SilentlyContinue).Source
if (-not $uvPath) {
    $uvPath = Join-Path $env:USERPROFILE '.local\bin\uv.exe'
}
if (-not (Test-Path $uvPath)) {
    $uvPath = Join-Path $env:LOCALAPPDATA 'Microsoft\WinGet\Links\uv.exe'
}
if (-not (Test-Path $uvPath)) {
    Write-Err 'uv.exe 위치를 찾을 수 없습니다.'
    Read-Host '   Enter 로 종료'
    exit 1
}

Write-Host '   uvx 로 caselaw-mcp 미리 받습니다 (Python 자동 다운로드 포함, 30초~3분)...'
$installExit = -999
$installOutput = $null
$prevEAP = $ErrorActionPreference
$ErrorActionPreference = 'Continue'  # uv 의 stderr 진행 메시지가 throw 되지 않게
try {
    $installOutput = & $uvPath tool install caselaw-mcp 2>&1
    $installExit = $LASTEXITCODE
} catch {
    Write-Warn "tool install 호출 중 예외: $($_.Exception.Message)"
    $installExit = -1
}
$ErrorActionPreference = $prevEAP

if ($installExit -eq 0) {
    Write-Ok 'caselaw-mcp 설치 완료'
} else {
    Write-Warn "tool install 정상 완료 안 됨 (exit=$installExit). uvx 가 첫 호출 시 자동으로 받으므로 계속 진행합니다."
}

# ─────────────────────────────────────────────
# 4. Claude Desktop config 자동 작성
# ─────────────────────────────────────────────
Write-Step '4단계: Claude Desktop 설정 자동 작성'

$configPath = Join-Path $configDir 'claude_desktop_config.json'

# 기존 config 백업
if (Test-Path $configPath) {
    $backup = "$configPath.backup-$(Get-Date -Format yyyyMMdd-HHmmss)"
    Copy-Item $configPath $backup
    Write-Ok "기존 설정 백업: $backup"
    $rawJson = Get-Content $configPath -Raw -Encoding UTF8
    if ([string]::IsNullOrWhiteSpace($rawJson)) { $rawJson = '{}' }
} else {
    $rawJson = '{}'
}

# 기존 config 안전 파싱 (실패해도 진행)
$cur = $null
try {
    $cur = $rawJson | ConvertFrom-Json -ErrorAction Stop
} catch {
    Write-Warn "기존 config 파싱 실패 → 새로 작성: $($_.Exception.Message)"
    $cur = $null
}

# PSCustomObject -> ordered Hashtable 변환 (빈 PSCustomObject 의 Add-Member 이슈 회피)
function _ToHashtable {
    param($obj)
    if ($null -eq $obj) { return [ordered]@{} }
    if ($obj -is [PSCustomObject]) {
        $ht = [ordered]@{}
        foreach ($p in $obj.PSObject.Properties) { $ht[$p.Name] = _ToHashtable $p.Value }
        return $ht
    }
    if ($obj -is [System.Collections.IDictionary]) {
        $ht = [ordered]@{}
        foreach ($k in $obj.Keys) { $ht[$k] = _ToHashtable $obj[$k] }
        return $ht
    }
    if ($obj -is [System.Array]) {
        return @($obj | ForEach-Object { _ToHashtable $_ })
    }
    return $obj
}

$config = _ToHashtable $cur
if ($config -isnot [System.Collections.IDictionary]) { $config = [ordered]@{} }
if (-not $config.Contains('mcpServers') -or $config['mcpServers'] -isnot [System.Collections.IDictionary]) {
    $config['mcpServers'] = [ordered]@{}
}

# caselaw 항목을 직접 키 할당 (Add-Member 안 씀)
$config['mcpServers']['caselaw'] = [ordered]@{
    command = 'uvx'
    args    = @('caselaw-mcp')
    env     = [ordered]@{ CASELAW_OC = $ocKey }
}

$jsonOut = $config | ConvertTo-Json -Depth 10
[System.IO.File]::WriteAllText($configPath, $jsonOut, [System.Text.UTF8Encoding]::new($false))

Write-Ok "설정 파일 작성: $configPath"

# 검증 — 작성한 파일을 다시 읽어 caselaw 가 진짜 등록됐는지 확인
try {
    $verify = Get-Content $configPath -Raw -Encoding UTF8 | ConvertFrom-Json -ErrorAction Stop
    if ($verify.mcpServers.caselaw.command -eq 'uvx') {
        Write-Ok '검증: mcpServers.caselaw 정상 등록 확인'
    } else {
        Write-Err '검증 실패! caselaw 항목이 누락됐습니다. 메모장으로 직접 추가해주세요.'
        Write-Host '   생성된 파일 내용:' -ForegroundColor DarkGray
        Get-Content $configPath -Raw
    }
} catch {
    Write-Err "검증 중 오류: $($_.Exception.Message)"
}

# ─────────────────────────────────────────────
# 5. 마무리 안내
# ─────────────────────────────────────────────
Write-Step '5단계: 설치 완료'

Write-Host ''
Write-Host '   모든 설정이 끝났습니다!' -ForegroundColor Green
Write-Host ''
Write-Host '   다음 절차로 사용하세요:'
Write-Host ''
Write-Host '   1) 시계 옆 트레이의 Claude Desktop 아이콘 -> Quit (이미 켜져 있다면)'
Write-Host '   2) 시작 메뉴에서 Claude Desktop 다시 실행'
Write-Host '   3) 채팅창에 다음과 같이 입력해보세요:'
Write-Host ''
Write-Host '         caselaw 로 ping 해줘' -ForegroundColor Yellow
Write-Host ''
Write-Host '      -> 응답에 oc_configured: true 가 나오면 성공입니다.'
Write-Host ''
Write-Host '   4) 실제 검색 예시:'
Write-Host ''
Write-Host '         음주운전 양형 5건 사건번호와 함께 표로 정리해줘' -ForegroundColor Yellow
Write-Host '         3년 전 친구한테 5천만원 빌려줬는데 안 갚아요. 어떻게 해야 하죠?' -ForegroundColor Yellow
Write-Host ''
Write-Host '   문제 발생 시:'
Write-Host '     - https://github.com/lapiogga/caseLaw/issues 에 신고'
Write-Host '     - 또는 위 백업 파일로 복원 가능'
Write-Host ''
Read-Host '   아무 키나 누르면 창이 닫힙니다'
