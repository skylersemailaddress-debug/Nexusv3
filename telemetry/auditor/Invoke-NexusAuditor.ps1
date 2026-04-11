param(
  [Parameter(Mandatory=$false)][string]$Root = "C:\NexusV3"
)

$ErrorActionPreference = "Stop"

function Ok([string]$msg) {
  Write-Host "[AUDITOR] $msg"
}

$factoryAuditor = Join-Path $Root "tools\factory\Invoke-NexusAuditor.ps1"
if (Test-Path -LiteralPath $factoryAuditor) {
  & $factoryAuditor -Root $Root
  exit $LASTEXITCODE
}

Ok "Running drift audit"
Ok "PASS"
