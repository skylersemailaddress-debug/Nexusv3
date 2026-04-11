param(
  [Parameter(Mandatory=$true)][string]$Source,
  [Parameter(Mandatory=$false)][string]$Subsystem = "unclassified",
  [Parameter(Mandatory=$false)][string]$Root = "C:\NexusV3"
)

$ErrorActionPreference = "Stop"
& (Join-Path $Root "tools\extraction\Invoke-NexusExtraction.ps1") -Root $Root -Source $Source -Subsystem $Subsystem
