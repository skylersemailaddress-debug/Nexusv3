param(
  [string]$NexusRoot = "C:\NexusV3",
  [string]$QuarantineRoot = "C:\NexusQuarantine"
)
$ErrorActionPreference = "Stop"
& (Join-Path $NexusRoot "tools\packout\Invoke-NexusPhase9Packout.ps1") -NexusRoot $NexusRoot -QuarantineRoot $QuarantineRoot
