# Use a named existing connection; credentials remain in its protected config file.
param(
    [string]$ConnectionName = 'snowflake-DINHEAO-HN84194',
    [string]$ConfigPath = "$env:LOCALAPPDATA\snowflake\config.toml",
    [string]$Role = 'AGENT_ROLE',
    [string]$Warehouse = 'POC_WH',
    [ValidateSet('intelligence','desk')]
    [string]$App = 'intelligence',
    [int]$Port = 0
)
$env:TUNE_SNOWFLAKE_CONNECTION = $ConnectionName
$env:TUNE_SNOWFLAKE_CONFIG = $ConfigPath
$env:TUNE_SNOWFLAKE_ROLE = $Role
$env:TUNE_SNOWFLAKE_WAREHOUSE = $Warehouse
$entryPoint = if ($App -eq 'desk') { 'apps\data-service-desk\app.py' } else { 'apps\ai-intelligence\app.py' }
if ($Port -eq 0) { $Port = if ($App -eq 'desk') { 8502 } else { 8501 } }
Push-Location -LiteralPath $PSScriptRoot
try {
    & "$PSScriptRoot\.venv\Scripts\python.exe" -m streamlit run "$PSScriptRoot\$entryPoint" --server.port $Port
} finally {
    Pop-Location
}
