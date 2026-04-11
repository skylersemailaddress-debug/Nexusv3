param(
  [string]$NexusRoot = 'C:\NexusV3',
  [string]$QuarantineRoot = 'C:\NexusQuarantine'
)
$ErrorActionPreference = 'Stop'
& (Join-Path $NexusRoot 'tools\extraction\Invoke-NexusPhase3Extractor.ps1') -NexusRoot $NexusRoot -QuarantineRoot $QuarantineRoot
