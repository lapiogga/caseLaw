# Gemini CLI 의 settings.json 에 caselaw MCP 서버 등록.
# 기존 mcpServers 등은 보존. 어떤 사용자/경로에서도 작동하도록 동적 경로 사용.
#
# Usage:
#   .\scripts\install-caselaw-gemini.ps1
#
# Optional:
#   -ProjectRoot <path>   기본: 스크립트 위치의 부모 (이 레포 루트)
#   -UvPath <path>        기본: 자동 탐색 (winget / .local / PATH)
#   -UseUvx               PyPI 의 uvx 방식 사용 (로컬 클론 대신, --directory 없이)

param(
    [string]$ProjectRoot,
    [string]$UvPath,
    [switch]$UseUvx
)

$ErrorActionPreference = 'Stop'

# ─────────────────────────────────────────────
# 1. 프로젝트 경로 자동 탐지 (UseUvx 모드는 사용 안 함)
# ─────────────────────────────────────────────
if (-not $ProjectRoot) {
    $ProjectRoot = Split-Path -Parent $PSScriptRoot
}
$ProjectRoot = (Resolve-Path $ProjectRoot).Path

if (-not (Test-Path (Join-Path $ProjectRoot 'pyproject.toml'))) {
    throw "유효한 프로젝트 루트가 아님 (pyproject.toml 없음): $ProjectRoot"
}
Write-Host "Project root: $ProjectRoot"

# ─────────────────────────────────────────────
# 2. uv / uvx 탐지
# ─────────────────────────────────────────────
function Find-Executable {
    param([string[]]$Candidates)
    foreach ($c in $Candidates) {
        $resolved = Get-Command $c -ErrorAction SilentlyContinue
        if ($resolved) { return $resolved.Source }
    }
    return $null
}

if ($UseUvx) {
    $UvxPath = Find-Executable @(
        (Join-Path $env:USERPROFILE '.local\bin\uvx.exe'),
        (Join-Path $env:LOCALAPPDATA 'Microsoft\WinGet\Links\uvx.exe'),
        'uvx.exe'
    )
    if (-not $UvxPath) {
        throw "uvx.exe 를 찾을 수 없음. uv 를 먼저 설치 (irm https://astral.sh/uv/install.ps1 | iex)"
    }
    Write-Host "uvx: $UvxPath"
} else {
    if (-not $UvPath) {
        $UvPath = Find-Executable @(
            (Join-Path $env:USERPROFILE '.local\bin\uv.exe'),
            (Join-Path $env:LOCALAPPDATA 'Microsoft\WinGet\Links\uv.exe'),
            'uv.exe'
        )
    }
    if (-not $UvPath -or -not (Test-Path $UvPath)) {
        throw "uv.exe 를 찾을 수 없음. -UvPath 로 직접 지정하거나 uv 를 먼저 설치"
    }
    Write-Host "uv: $UvPath"
}

# ─────────────────────────────────────────────
# 3. Gemini settings.json 위치 탐지
# ─────────────────────────────────────────────
$geminiDir = Join-Path $env:USERPROFILE '.gemini'
$settingsPath = Join-Path $geminiDir 'settings.json'

if (-not (Test-Path $geminiDir)) {
    New-Item -ItemType Directory -Path $geminiDir -Force | Out-Null
    Write-Host "신규 디렉토리 생성: $geminiDir"
}

if (-not (Test-Path $settingsPath)) {
    '{}' | Set-Content -Path $settingsPath -Encoding UTF8
    Write-Host "신규 settings.json 생성: $settingsPath"
} else {
    Write-Host "Found settings: $settingsPath"
}

# ─────────────────────────────────────────────
# 4. 백업
# ─────────────────────────────────────────────
$backup = "$settingsPath.backup-$(Get-Date -Format yyyyMMdd-HHmmss)"
Copy-Item $settingsPath $backup
Write-Host "Backup created: $backup"

# ─────────────────────────────────────────────
# 5. 기존 settings.json 병합 (mcpServers.caselaw 만 갱신, 나머지 보존)
# ─────────────────────────────────────────────
$rawJson = Get-Content $settingsPath -Raw
if ([string]::IsNullOrWhiteSpace($rawJson)) { $rawJson = '{}' }
$cur = $rawJson | ConvertFrom-Json

if ($UseUvx) {
    $caselawEntry = @{
        command = $UvxPath
        args    = @('caselaw-mcp')
        timeout = 30000
    }
} else {
    $caselawEntry = @{
        command = $UvPath
        args    = @('run', '--directory', $ProjectRoot, 'caselaw-mcp')
        cwd     = $ProjectRoot
        timeout = 30000
    }
}

if (-not ($cur.PSObject.Properties.Name -contains 'mcpServers')) {
    $cur | Add-Member -NotePropertyName mcpServers -NotePropertyValue (@{}) -Force
}
# mcpServers 가 PSCustomObject 일 수도, hashtable 일 수도. 항상 caselaw 노드 갱신.
if ($cur.mcpServers -is [hashtable]) {
    $cur.mcpServers['caselaw'] = $caselawEntry
} else {
    $cur.mcpServers | Add-Member -NotePropertyName caselaw -NotePropertyValue $caselawEntry -Force
}

$json = $cur | ConvertTo-Json -Depth 10
[System.IO.File]::WriteAllText($settingsPath, $json, [System.Text.UTF8Encoding]::new($false))

Write-Host ''
Write-Host '=== 새 settings 내용 ==='
Get-Content $settingsPath -Raw

Write-Host ''
$reparsed = Get-Content $settingsPath -Raw | ConvertFrom-Json
Write-Host ('등록된 MCP 서버: ' + ($reparsed.mcpServers.PSObject.Properties.Name -join ', '))

Write-Host ''
Write-Host '다음 단계:'
Write-Host '  1. PowerShell 새 창에서: gemini mcp list   (caselaw 표시 확인)'
Write-Host '  2. gemini   세션 시작'
Write-Host '  3. 자연어 호출: "caselaw 의 ping 도구 호출해 줘"'
Write-Host ''
Write-Host '주의: Gemini CLI 가 미설치라면 https://github.com/google-gemini/gemini-cli 에서 설치 후 본 명령 재실행'
