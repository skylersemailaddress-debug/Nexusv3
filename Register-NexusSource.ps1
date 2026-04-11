param(
  [Parameter(Mandatory=$true)][string]$Name,
  [Parameter(Mandatory=$true)][string]$Path,
  [Parameter(Mandatory=$true)][string]$Subsystem,
  [Parameter(Mandatory=$false)][string]$Root = "C:\NexusV3",
  [Parameter(Mandatory=$false)][string]$Notes = "",
  [switch]$Disabled
)

$ErrorActionPreference = "Stop"
& (Join-Path $Root "tools\extraction\Register-NexusSource.ps1") -Root $Root -Name $Name -Path $Path -Subsystem $Subsystem -Notes $Notes -Disabled:$Disabled
