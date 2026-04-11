$ErrorActionPreference = 'Stop'
$ops = $PSScriptRoot
Write-Host "Starting Nexus API in a new window..."
Start-Process powershell -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File', (Join-Path $ops 'start-api.ps1'))
Start-Sleep -Seconds 2
Write-Host "Starting Nexus UI in a new window..."
Start-Process powershell -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File', (Join-Path $ops 'start-ui.ps1'))
Write-Host "Nexus API: http://127.0.0.1:8000/health"
Write-Host "Nexus UI : http://127.0.0.1:5173"
Write-Host "Then run: .\\validate.ps1"
