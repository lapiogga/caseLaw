# Claude Desktop (MSIX 컨테이너) 의 진짜 config 에 caselaw MCP 서버 등록.
# 기존 preferences 등 보존. 어떤 사용자/경로에서도 작동하도록 동적 경로 사용.
#
# Usage:
#   .\scripts\install-caselaw-mcp.ps1
#
# Optional:
#   -ProjectRoot <path>   기본: 스크립트 위치의 부모 (이 레포 루트)
#   -UvPath <path>        기본: 자동 탐색 (winget / .local / PATH)

param(
    [string]$ProjectRoot,
    [string]$UvPath
)

$ErrorActionPreference = 'Stop'

# ─────────────────────────────────────────────
# 1. 프로젝트 경로 자동 탐지
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
# 2. uv 실행파일 탐지
# ─────────────────────────────────────────────
if (-not $UvPath) {
    $candidates = @(
        (Join-Path $env:USERPROFILE '.local\bin\uv.exe'),
        (Join-Path $env:LOCALAPPDATA 'Microsoft\WinGet\Links\uv.exe'),
        'uv.exe'
    )
    foreach ($c in $candidates) {
        $resolved = Get-Command $c -ErrorAction SilentlyContinue
        if ($resolved) { $UvPath = $resolved.Source; break }
    }
}
if (-not $UvPath -or -not (Test-Path $UvPath)) {
    throw "uv.exe 를 찾을 수 없음. -UvPath 로 직접 지정하거나 uv 를 먼저 설치 (winget install astral-sh.uv)"
}
Write-Host "uv: $UvPath"

# ─────────────────────────────────────────────
# 3. Claude Desktop config 위치 탐지 (MSIX 우선, 일반 설치 fallback)
# ─────────────────────────────────────────────
$configCandidates = @(
    (Join-Path $env:LOCALAPPDATA 'Packages\Claude_pzs8sxrjxfjjc\LocalCache\Roaming\Claude\claude_desktop_config.json'),
    (Join-Path $env:APPDATA 'Claude\claude_desktop_config.json')
)
$real = $null
foreach ($c in $configCandidates) {
    if (Test-Path $c) { $real = $c; break }
}
if (-not $real) {
    # MSIX 가 우선 — 디렉토리만 존재하면 빈 config 작성
    $msixDir = Split-Path $configCandidates[0] -Parent
    $appDataDir = Split-Path $configCandidates[1] -Parent
    if (Test-Path $msixDir) {
        $real = $configCandidates[0]
    } elseif (Test-Path $appDataDir) {
        $real = $configCandidates[1]
    } else {
        throw "Claude Desktop 이 설치되지 않음. 먼저 https://claude.ai/download 에서 설치 후 한번 실행."
    }
    '{}' | Set-Content -Path $real -Encoding UTF8
    Write-Host "신규 config 생성: $real"
} else {
    Write-Host "Found config: $real"
}

# ─────────────────────────────────────────────
# 4. 백업
# ─────────────────────────────────────────────
$backup = "$real.backup-$(Get-Date -Format yyyyMMdd-HHmmss)"
Copy-Item $real $backup
Write-Host "Backup created: $backup"

# ─────────────────────────────────────────────
# 5. 기존 config 병합 (mcpServers.caselaw 만 갱신, 나머지 보존)
# ─────────────────────────────────────────────
$rawJson = Get-Content $real -Raw
if ([string]::IsNullOrWhiteSpace($rawJson)) { $rawJson = '{}' }
$cur = $rawJson | ConvertFrom-Json

$caselawEntry = @{
    command = $UvPath
    args    = @('run', '--directory', $ProjectRoot, 'caselaw-mcp')
}

if (-not $cur.PSObject.Properties.Name -contains 'mcpServers') {
    $cur | Add-Member -NotePropertyName mcpServers -NotePropertyValue (@{}) -Force
}
$cur.mcpServers | Add-Member -NotePropertyName caselaw -NotePropertyValue $caselawEntry -Force

$json = $cur | ConvertTo-Json -Depth 10
[System.IO.File]::WriteAllText($real, $json, [System.Text.UTF8Encoding]::new($false))

Write-Host ''
Write-Host '=== 새 config 내용 ==='
Get-Content $real -Raw

Write-Host ''
$reparsed = Get-Content $real -Raw | ConvertFrom-Json
Write-Host ('등록된 MCP 서버: ' + ($reparsed.mcpServers.PSObject.Properties.Name -join ', '))
Write-Host ''
Write-Host '다음 단계:'
Write-Host '  1. Claude Desktop 완전 종료 (트레이 → Quit)'
Write-Host '  2. Claude Desktop 다시 실행'
Write-Host '  3. 채팅창에 "caselaw 로 ping 해줘" 입력'
