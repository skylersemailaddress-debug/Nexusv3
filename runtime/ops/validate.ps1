$authHeaders = @{ Authorization = "Bearer dev-operator-token" }

Write-Host "Checking API health..."
$health = Invoke-RestMethod 'http://127.0.0.1:8000/health'
if ($health.status -ne 'ok') { throw 'API health failed' }
Write-Host "API OK"

Write-Host "Checking API action route..."
$action = Invoke-RestMethod -Method Post 'http://127.0.0.1:8000/action/test' -Headers $authHeaders -ContentType 'application/json' -Body '{"source":"validator"}'
if (-not $action.result) { throw 'API action failed' }
Write-Host "API action OK"

Write-Host "Checking dashboard status route..."
$status = Invoke-RestMethod 'http://127.0.0.1:8000/dashboard/status' -Headers $authHeaders
if (-not $status.status) { throw 'Dashboard status failed' }
Write-Host "Dashboard status OK"

Write-Host "Checking UI reachability..."
try {
  $ui = Invoke-WebRequest 'http://127.0.0.1:5173' -UseBasicParsing
  if ($ui.StatusCode -lt 200 -or $ui.StatusCode -ge 400) { throw 'UI status code not OK' }
  Write-Host "UI OK"
} catch {
  throw "UI reachability failed: $($_.Exception.Message)"
}

Write-Host "Nexus runtime validation PASSED"
