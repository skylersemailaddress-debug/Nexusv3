param(
  [Parameter(Mandatory=$true)][string]$NexusRoot,
  [Parameter(Mandatory=$true)][string]$QuarantineRoot,
  [string]$SourceRoot = 'C:\NexusArchiveDrop',
  [switch]$ExpandAll
)
$ErrorActionPreference = 'Stop'
$expandScript = Join-Path $NexusRoot 'tools\intake\Expand-And-Register-NexusArchiveSet.ps1'
if (-not (Test-Path $expandScript)) {
  throw "Missing required script: $expandScript"
}
if (-not (Test-Path $SourceRoot)) {
  throw "Missing source root: $SourceRoot"
}
Write-Host "[AUTO-ARCHIVE-INTAKE] Using staged source root: $SourceRoot"
& $expandScript -SourceRoot $SourceRoot -NexusRoot $NexusRoot -QuarantineRoot $QuarantineRoot -ExpandAll:$ExpandAll
