# Use a named existing connection; credentials remain in its protected config file.
param(
    [string]$ConnectionName = 'snowflake-DINHEAO-HN84194',
    [string]$ConfigPath = "$env:LOCALAPPDATA\snowflake\config.toml",
    [string]$Role = 'AGENT_ROLE',
    [string]$Warehouse = 'POC_WH',
    [ValidateSet('intelligence','desk','both','react')]
    [string]$App = 'intelligence',
    [ValidateRange(0,65535)]
    [int]$Port = 0
)
$env:TUNE_SNOWFLAKE_CONNECTION = $ConnectionName
$env:TUNE_SNOWFLAKE_CONFIG = $ConfigPath
$env:TUNE_SNOWFLAKE_ROLE = $Role
$env:TUNE_SNOWFLAKE_WAREHOUSE = $Warehouse
if ($App -eq 'react') {
    $reactPort = if ($Port -eq 0) { 8000 } else { $Port }
    & "$PSScriptRoot\launch-react.ps1" -ConnectionName $ConnectionName -ConfigPath $ConfigPath -Role $Role -Warehouse $Warehouse -Port $reactPort
    return
}
if ($App -eq 'both') {
    $ErrorActionPreference = 'Stop'
    $firstPort = if ($Port -eq 0) { 8501 } else { $Port }
    if ($firstPort -eq 65535) { throw 'Both apps need two consecutive ports; choose -Port below 65535.' }
    $targets = @(
        @{ Name='intelligence'; Entry='apps\ai-intelligence\app.py'; Port=$firstPort },
        @{ Name='desk'; Entry='apps\data-service-desk\app.py'; Port=($firstPort + 1) }
    )
    foreach ($target in $targets) {
        $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, $target.Port)
        try { $listener.Start() }
        catch { throw "Port $($target.Port) is already in use. Stop that app or choose another -Port." }
        finally { $listener.Stop() }
    }
    $python = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $python)) { throw 'Install the virtual environment first; see README.md.' }
    $logs = Join-Path $PSScriptRoot 'validation'
    New-Item -ItemType Directory -Force -Path $logs | Out-Null
    $processes = @()
    try {
        foreach ($target in $targets) {
            $entry = Join-Path $PSScriptRoot $target.Entry
            $arguments = @('-m','streamlit','run',('"' + $entry + '"'),'--server.port',$target.Port,'--browser.gatherUsageStats','false')
            $processes += Start-Process -FilePath $python -ArgumentList $arguments -WorkingDirectory $PSScriptRoot -WindowStyle Hidden -PassThru `
                -RedirectStandardOutput "$logs\$($target.Name)-launch.log" -RedirectStandardError "$logs\$($target.Name)-launch-error.log"
            Write-Host "$($target.Name): http://localhost:$($target.Port)"
        }
        Write-Host 'Press Ctrl+C here to stop both apps. Server output is in validation/*-launch*.log.'
        while ($true) {
            foreach ($process in $processes) {
                if ($process.HasExited) { throw 'An app exited. Check validation/*-launch-error.log for details.' }
            }
            Start-Sleep -Milliseconds 500
        }
    } finally {
        # Stop the venv launcher's child interpreter as well as its parent.
        foreach ($process in $processes) {
            if (-not $process.HasExited) {
                & taskkill.exe /PID $process.Id /T /F 2>$null | Out-Null
            }
        }
    }
    return
}
$entryPoint = if ($App -eq 'desk') { 'apps\data-service-desk\app.py' } else { 'apps\ai-intelligence\app.py' }
if ($Port -eq 0) { $Port = if ($App -eq 'desk') { 8502 } else { 8501 } }
Push-Location -LiteralPath $PSScriptRoot
try {
    & "$PSScriptRoot\.venv\Scripts\python.exe" -m streamlit run "$PSScriptRoot\$entryPoint" --server.port $Port
} finally {
    Pop-Location
}
