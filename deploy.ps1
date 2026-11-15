# Stage one app and the common source for Snowflake CLI's project-root boundary.
param(
    [ValidateSet('intelligence','desk')]
    [string]$App = 'intelligence',
    [string]$ConnectionName = 'snowflake-DINHEAO-HN84194',
    [string]$Role = 'AGENT_ROLE',
    [string]$Warehouse = 'POC_WH',
    [switch]$PrepareOnly
)
$ErrorActionPreference = 'Stop'
$appFolder = if ($App -eq 'desk') { 'data-service-desk' } else { 'ai-intelligence' }
$entity = if ($App -eq 'desk') { 'tune_desk' } else { 'tune_ai' }
$source = Join-Path $PSScriptRoot "apps\$appFolder"
$bundle = Join-Path $PSScriptRoot "output\deploy\$App"
New-Item -ItemType Directory -Force -Path $bundle, "$bundle\shared\assets", "$bundle\.streamlit" | Out-Null
Copy-Item -LiteralPath "$source\app.py", "$source\snowflake.yml" -Destination $bundle -Force
Get-ChildItem -LiteralPath "$PSScriptRoot\shared" -Filter '*.py' -File |
    Copy-Item -Destination "$bundle\shared" -Force
Get-ChildItem -LiteralPath "$PSScriptRoot\shared\assets" -Filter '*.png' -File |
    Copy-Item -Destination "$bundle\shared\assets" -Force
Copy-Item -LiteralPath "$PSScriptRoot\shared\environment.yml" -Destination "$bundle\environment.yml" -Force
Copy-Item -LiteralPath "$PSScriptRoot\.streamlit\config.toml" -Destination "$bundle\.streamlit\config.toml" -Force
if ($PrepareOnly) {
    Write-Output $bundle
    return
}
$deployArgs = @('streamlit', 'deploy', $entity, '--project', $bundle,
    '--connection', $ConnectionName, '--role', $Role, '--warehouse', $Warehouse,
    '--database', 'TUNE_BI_DB', '--schema', 'APP_STATE', '--replace')
& snow @deployArgs
exit $LASTEXITCODE
