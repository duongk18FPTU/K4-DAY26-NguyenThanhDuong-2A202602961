param(
    [ValidateSet('Server', 'Client', 'Verify')]
    [string]$Target = 'Server',
    [switch]$Live
)

$ErrorActionPreference = 'Stop'
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'

$project = if ($Target -eq 'Server') { 'mcp-server' } else { 'mcp-client' }
$projectPath = Join-Path $PSScriptRoot $project
$pythonPath = Join-Path $projectPath '.venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $pythonPath)) {
    throw "Missing environment: $pythonPath. See SETUP-WINDOWS.md."
}

Push-Location $projectPath
try {
    switch ($Target) {
        'Server' {
            & $pythonPath weather.py
        }
        'Client' {
            & (Join-Path $projectPath '.venv/Scripts/adk.exe') web --host 127.0.0.1 --port 8000 --no-reload
        }
        'Verify' {
            if ($Live) { & $pythonPath verify_setup.py --live }
            else { & $pythonPath verify_setup.py }
        }
    }
    $result = $LASTEXITCODE
}
finally {
    Pop-Location
}
exit $result
