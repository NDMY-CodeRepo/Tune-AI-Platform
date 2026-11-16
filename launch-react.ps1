# Local same-origin React + Python API; credentials stay in the existing profile.
param(
    [string]$ConnectionName = 'snowflake-DINHEAO-HN84194',
    [string]$ConfigPath = "$env:LOCALAPPDATA\snowflake\config.toml",
    [string]$Role = 'AGENT_ROLE',
    [string]$Warehouse = 'POC_WH',
    [ValidateRange(1024,65535)][int]$Port = 8000,
    [switch]$SkipBuild
)
$ErrorActionPreference = 'Stop'
$env:TUNE_SNOWFLAKE_CONNECTION = $ConnectionName
$env:TUNE_SNOWFLAKE_CONFIG = $ConfigPath
$env:TUNE_SNOWFLAKE_ROLE = $Role
$env:TUNE_SNOWFLAKE_WAREHOUSE = $Warehouse
$python = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python)) { throw 'Create the Python virtual environment first; see README.md.' }
$listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback,$Port)
try { $listener.Start() } catch { throw "Port $Port is already in use. Choose another -Port." } finally { $listener.Stop() }
Push-Location $PSScriptRoot
try {
    $apiDependencies = & $python -c "import importlib.util; print(all(importlib.util.find_spec(m) is not None for m in ['fastapi','uvicorn']))"
    if ($apiDependencies -ne 'True') {
        & $python -m pip install -r apps/api/requirements.txt
        if ($LASTEXITCODE -ne 0) { throw 'API dependency installation failed.' }
    }
    if (-not $SkipBuild) {
        Push-Location apps/ai-intelligence-react
        try {
            if (-not (Test-Path -LiteralPath node_modules)) {
                & npm.cmd ci --no-fund
                if ($LASTEXITCODE -ne 0) { throw 'Frontend dependency installation failed.' }
            }
            & npm.cmd run build
            if ($LASTEXITCODE -ne 0) { throw 'Frontend build failed.' }
        } finally { Pop-Location }
    }
    if (-not (Test-Path -LiteralPath apps/ai-intelligence-react/dist/index.html)) { throw 'Frontend build missing. Run without -SkipBuild.' }
    Write-Host "Tune AI Intelligence: http://127.0.0.1:$Port"
    Write-Host 'Local demo only. Press Ctrl+C to stop. Streamlit remains available through launch.ps1.'
    & $python -m uvicorn apps.api.main:app --host 127.0.0.1 --port $Port
} finally { Pop-Location }
