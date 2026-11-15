# Use a named existing connection; credentials remain in its protected config file.
param(
    [string]$ConnectionName = 'snowflake-DINHEAO-HN84194',
    [string]$ConfigPath = "$env:LOCALAPPDATA\snowflake\config.toml",
    [string]$Role = 'AGENT_ROLE',
    [string]$Warehouse = 'POC_WH'
)
$env:TUNE_SNOWFLAKE_CONNECTION = $ConnectionName
$env:TUNE_SNOWFLAKE_CONFIG = $ConfigPath
$env:TUNE_SNOWFLAKE_ROLE = $Role
$env:TUNE_SNOWFLAKE_WAREHOUSE = $Warehouse
& "$PSScriptRoot\.venv\Scripts\python.exe" -m streamlit run "$PSScriptRoot\app.py"
