Write-Host "Stopping prior Nexus runtime processes on ports 8000 and 5173 if present..."

$ports = @(8000, 5173)
foreach ($p in $ports) {
  try {
    $conns = Get-NetTCPConnection -LocalPort $p -State Listen -ErrorAction Stop
    foreach ($c in $conns) {
      try {
        Stop-Process -Id $c.OwningProcess -Force -ErrorAction Stop
        Write-Host "Stopped process $($c.OwningProcess) on port $p"
      } catch {
        Write-Host ("Could not stop process {0} on port {1}: {2}" -f $c.OwningProcess, $p, $_.Exception.Message)
      }
    }
  } catch {
    Write-Host "No listening process found on port $p"
  }
}

Start-Sleep -Seconds 1

Write-Host "Starting clean Nexus runtime..."
& (Join-Path $PSScriptRoot 'start-all.ps1')
