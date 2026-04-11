param(
  [Parameter(Mandatory=$false)][string]$Root = "C:\NexusV3",
  [Parameter(Mandatory=$false)][string]$QuarantineRoot = "C:\NexusQuarantine",
  [Parameter(Mandatory=$false)][string]$DownloadsRoot = "$env:USERPROFILE\Downloads"
)

$ErrorActionPreference = "Stop"
& (Join-Path $Root "tools\extraction\Expand-And-Register-NexusArchives.ps1") -Root $Root -QuarantineRoot $QuarantineRoot -DownloadsRoot $DownloadsRoot
