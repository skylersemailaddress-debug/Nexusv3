param(
  [Parameter(Mandatory=$true)][string]$NexusRoot,
  [Parameter(Mandatory=$true)][string]$QuarantineRoot
)
$ErrorActionPreference = 'Stop'
& (Join-Path $NexusRoot 'tools\planning\Invoke-NexusPhase2MergePlanner.ps1') -NexusRoot $NexusRoot -QuarantineRoot $QuarantineRoot
