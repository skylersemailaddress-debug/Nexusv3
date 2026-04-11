$ErrorActionPreference = 'Stop'
Write-Host "Checking API health..."
$health = Invoke-RestMethod 'http://127.0.0.1:8000/health'
if ($health.status -ne 'ok') { throw 'API health failed' }
Write-Host "API OK"

Write-Host "Checking API action route..."
$payload = @{ probe = 'runtime-validator' } | ConvertTo-Json
$action = Invoke-RestMethod -Method Post 'http://127.0.0.1:8000/action/test' -ContentType 'application/json' -Body $payload
if (-not $action.result) { throw 'API action failed' }
Write-Host "API action OK"

Write-Host "Checking dashboard status route..."
$dash = Invoke-RestMethod 'http://127.0.0.1:8000/dashboard/status'
if ($dash.status -ne 'ok') { throw 'Dashboard status failed' }
Write-Host "Dashboard status OK"

Write-Host "Checking UI reachability..."
try {
  $ui = Invoke-WebRequest 'http://127.0.0.1:5173' -UseBasicParsing
  if ($ui.StatusCode -lt 200 -or $ui.StatusCode -ge 400) { throw "Unexpected UI status: $($ui.StatusCode)" }
  Write-Host "UI OK"
} catch {
  throw "UI reachability failed: $($_.Exception.Message)"
}

Write-Host 'Nexus runtime validation PASSED'
