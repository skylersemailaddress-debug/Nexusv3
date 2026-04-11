$ErrorActionPreference = 'Stop'

Write-Host 'Starting Nexus runtime control API...'
Start-Process powershell -WorkingDirectory (Join-Path $PSScriptRoot '..\control') -ArgumentList @(
  '-NoProfile',
  '-ExecutionPolicy','Bypass',
  '-Command',
  "python -m pip install -r requirements.txt; python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000"
)

Write-Host 'Starting Nexus runtime UI...'
Start-Process powershell -WorkingDirectory (Join-Path $PSScriptRoot '..\ui') -ArgumentList @(
  '-NoProfile',
  '-ExecutionPolicy','Bypass',
  '-Command',
  "cmd /c npm install && cmd /c npm run dev -- --host 127.0.0.1 --port 5173"
)

Write-Host 'API: http://127.0.0.1:8000/health'
Write-Host 'UI : http://127.0.0.1:5173'
Write-Host 'If UI still fails, run runtime\\ops\\start-ui.ps1 in a separate window to see npm errors.'
