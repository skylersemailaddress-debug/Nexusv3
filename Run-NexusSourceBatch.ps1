param(
  [Parameter(Mandatory=$false)][string]$OnlyName = "",
  [Parameter(Mandatory=$false)][string]$Root = "C:\NexusV3"
)

$ErrorActionPreference = "Stop"
& (Join-Path $Root "tools\extraction\Invoke-NexusSourceBatch.ps1") -Root $Root -OnlyName $OnlyName
