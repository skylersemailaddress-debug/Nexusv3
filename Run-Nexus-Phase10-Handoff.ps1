param(
  [string]$NexusRoot = "C:\NexusV3",
  [string]$QuarantineRoot = "C:\NexusQuarantine"
)
$ErrorActionPreference = "Stop"
& (Join-Path $NexusRoot "tools\handoff\Invoke-NexusPhase10Handoff.ps1") -NexusRoot $NexusRoot -QuarantineRoot $QuarantineRoot
