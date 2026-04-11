param(
  [string]$Root = "C:\NexusV3"
)
$ErrorActionPreference = "Stop"
& (Join-Path $Root "tools\canon\Compile-NexusCanon.ps1") -Root $Root
if (-not $?) { throw "Canon failed" }
& (Join-Path $Root "assembly\gates\Invoke-NexusGates.ps1") -Root $Root
if (-not $?) { throw "Gates failed" }
& (Join-Path $Root "telemetry\auditor\Invoke-NexusAuditor.ps1") -Root $Root
if (-not $?) { throw "Auditor failed" }
Write-Host "SHIP CHECK PASSED"
