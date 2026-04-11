param(
  [string]$NexusRoot = "C:\NexusV3",
  [string]$QuarantineRoot = "C:\NexusQuarantine"
)
$ErrorActionPreference = "Stop"
& (Join-Path $NexusRoot "tools\runtime\Invoke-NexusPhase7Runtime.ps1") -NexusRoot $NexusRoot -QuarantineRoot $QuarantineRoot
