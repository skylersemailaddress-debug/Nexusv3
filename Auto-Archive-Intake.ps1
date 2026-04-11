param(
  [Parameter(Mandatory=$true)][string]$NexusRoot,
  [Parameter(Mandatory=$true)][string]$QuarantineRoot,
  [switch]$ExpandAll
)
$ErrorActionPreference = 'Stop'
$invokeScript = Join-Path $NexusRoot 'tools\intake\Invoke-NexusAutoArchiveIntake.ps1'
if (-not (Test-Path $invokeScript)) {
  throw "Missing invoke script: $invokeScript"
}
& $invokeScript -NexusRoot $NexusRoot -QuarantineRoot $QuarantineRoot -SourceRoot 'C:\NexusArchiveDrop' -ExpandAll:$ExpandAll
