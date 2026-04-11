param(
  [ValidateSet("all","canon","gates","audit")][string]$Command = "all",
  [string]$Root = "C:\NexusV3"
)
$ErrorActionPreference = "Stop"
& (Join-Path $Root "tools\factory\Invoke-NexusFactory.ps1") -Command $Command -Root $Root
