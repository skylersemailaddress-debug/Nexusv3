param(
  [string]$NexusRoot = "C:\NexusV3",
  [string]$QuarantineRoot = "C:\NexusQuarantine"
)
$ErrorActionPreference = "Stop"
& (Join-Path $NexusRoot "tools\extraction\Invoke-NexusPhase4Executor.ps1") -NexusRoot $NexusRoot -QuarantineRoot $QuarantineRoot
