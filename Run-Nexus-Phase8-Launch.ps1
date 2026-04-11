param(
  [string]$NexusRoot = "C:\NexusV3",
  [string]$QuarantineRoot = "C:\NexusQuarantine"
)
$ErrorActionPreference = "Stop"
& (Join-Path $NexusRoot "tools\launch\Invoke-NexusPhase8Launch.ps1") -NexusRoot $NexusRoot -QuarantineRoot $QuarantineRoot
