param(
  [string]$NexusRoot = "C:\NexusV3",
  [string]$QuarantineRoot = "C:\NexusQuarantine"
)
$ErrorActionPreference = "Stop"
& (Join-Path $NexusRoot "tools\cleanup\Invoke-NexusCanonCleanup.ps1") -NexusRoot $NexusRoot -QuarantineRoot $QuarantineRoot
