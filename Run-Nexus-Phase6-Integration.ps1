param(
  [string]$NexusRoot = "C:\NexusV3",
  [string]$QuarantineRoot = "C:\NexusQuarantine"
)
$ErrorActionPreference = "Stop"
& (Join-Path $NexusRoot "tools\integration\Invoke-NexusPhase6Integration.ps1") -NexusRoot $NexusRoot -QuarantineRoot $QuarantineRoot
