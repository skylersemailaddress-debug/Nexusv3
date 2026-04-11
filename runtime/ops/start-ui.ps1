$ErrorActionPreference = 'Stop'
Set-Location (Join-Path $PSScriptRoot '..\ui')
cmd /c npm install
cmd /c npm run dev -- --host 127.0.0.1 --port 5173
