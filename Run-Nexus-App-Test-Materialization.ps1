param(
  [string]$NexusRoot = "C:\NexusV3",
  [string]$QuarantineRoot = "C:\NexusQuarantine"
)
$ErrorActionPreference = "Stop"
& (Join-Path $NexusRoot "tools\materialize\Invoke-NexusAppTestMaterialization.ps1") -NexusRoot $NexusRoot -QuarantineRoot $QuarantineRoot
