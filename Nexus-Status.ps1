param(
  [string]$Root = "C:\NexusV3"
)
$ErrorActionPreference = "Stop"
Write-Host "NexusRoot: $Root"
$checks = @(
  (Join-Path $Root "tools\factory\Invoke-NexusFactory.ps1"),
  (Join-Path $Root "tools\canon\Compile-NexusCanon.ps1"),
  (Join-Path $Root "assembly\gates\Invoke-NexusGates.ps1"),
  (Join-Path $Root "telemetry\auditor\Invoke-NexusAuditor.ps1")
)
foreach ($c in $checks) {
  if (Test-Path -LiteralPath $c) {
    Write-Host "[OK] $c"
  } else {
    Write-Host "[MISSING] $c"
    exit 1
  }
}
Write-Host "STATUS OK"
