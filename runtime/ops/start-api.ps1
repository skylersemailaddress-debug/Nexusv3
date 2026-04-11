$ErrorActionPreference = 'Stop'
Set-Location (Join-Path $PSScriptRoot '..\control')
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
