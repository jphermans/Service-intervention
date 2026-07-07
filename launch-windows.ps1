param(
    [int]$Port = $(if ($env:INTERVENTION_PORT) { [int]$env:INTERVENTION_PORT } else { 8000 }),
    [switch]$NoBrowser
)

$ErrorActionPreference = 'Stop'
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$DataDir = if ($env:INTERVENTION_DATA_DIR) { $env:INTERVENTION_DATA_DIR } else { Join-Path $ScriptDir 'data' }
$DbPath = if ($env:INTERVENTION_DB) { $env:INTERVENTION_DB } else { Join-Path $DataDir 'intervention_reports.sqlite3' }
$PythonHint = $env:INTERVENTION_PYTHON

New-Item -ItemType Directory -Force -Path $DataDir | Out-Null

function Test-Python([string]$Candidate) {
    if ([string]::IsNullOrWhiteSpace($Candidate)) { return $null }
    try {
        & $Candidate -c "import sqlite3, http.server" *> $null
        if ($LASTEXITCODE -eq 0) { return $Candidate }
    } catch { }
    return $null
}

$Python = $null
if ($PythonHint) { $Python = Test-Python $PythonHint }
if (-not $Python) { $Python = Test-Python (Join-Path $ScriptDir 'runtime\python\python.exe') }
if (-not $Python) { $Python = Test-Python (Join-Path $ScriptDir 'runtime\python\bin\python.exe') }
if (-not $Python) {
    foreach ($candidate in @('python3', 'python', 'py -3')) {
        try {
            if ($candidate -eq 'py -3') {
                & py -3 -c "import sqlite3, http.server" *> $null
                if ($LASTEXITCODE -eq 0) { $Python = 'py -3'; break }
            } else {
                $resolved = (Get-Command $candidate -ErrorAction SilentlyContinue).Source
                if ($resolved) {
                    $Python = Test-Python $resolved
                    if ($Python) { break }
                }
            }
        } catch { }
    }
}

if (-not $Python) {
    Write-Host 'Python 3 with sqlite3 was not found.' -ForegroundColor Yellow
    Write-Host 'Install Python 3 or place a runtime under runtime\python\python.exe.' -ForegroundColor Yellow
    exit 1
}

Set-Location $ScriptDir
$args = @('server.py', '--host', '127.0.0.1', '--port', $Port.ToString(), '--db', $DbPath)
if (-not $NoBrowser) { $args += '--open-browser' }

if ($Python -eq 'py -3') {
    & py -3 @args
} else {
    & $Python @args
}
