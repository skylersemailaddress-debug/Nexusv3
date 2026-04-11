param(
  [Parameter(Mandatory=$true)][string]$Root,
  [Parameter(Mandatory=$true)][string]$Source,
  [Parameter(Mandatory=$false)][string]$Subsystem = "unclassified"
)

$ErrorActionPreference = "Stop"
& (Join-Path $Root "tools\extraction\Apply-NexusExtraction.ps1") -Root $Root -Source $Source -Subsystem $Subsystem
