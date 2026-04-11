param(
  [Parameter(Mandatory=$false)][string]$Root = "C:\NexusV3",
  [Parameter(Mandatory=$false)][string]$QuarantineRoot = "C:\NexusQuarantine",
  [Parameter(Mandatory=$false)][string]$DownloadsRoot = "$env:USERPROFILE\Downloads"
)

$ErrorActionPreference = "Stop"

function Write-Info([string]$msg) {
  Write-Host "[ARCHIVE-INTAKE] $msg"
}

$manifestPath = Join-Path $Root "registry\sources\ARCHIVE_INTAKE_MANIFEST_V1.json"
$registerCmd = Join-Path $Root "Register-NexusSource.ps1"

if (-not (Test-Path -LiteralPath $manifestPath)) {
  throw "Archive intake manifest not found: $manifestPath"
}
if (-not (Test-Path -LiteralPath $registerCmd)) {
  throw "Register command not found: $registerCmd"
}

$manifest = Get-Content -LiteralPath $manifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
$incomingRoot = Join-Path $QuarantineRoot "incoming"
New-Item -ItemType Directory -Force -Path $incomingRoot | Out-Null

$processed = 0
$skipped = 0

foreach ($item in $manifest.archives) {
  $zipPath = Join-Path $DownloadsRoot $item.name
  if (-not (Test-Path -LiteralPath $zipPath)) {
    Write-Info "Skipping missing archive: $($item.name)"
    $skipped += 1
    continue
  }

  $dest = Join-Path $incomingRoot $item.extract_dir
  if (Test-Path -LiteralPath $dest) {
    Remove-Item -LiteralPath $dest -Recurse -Force -ErrorAction SilentlyContinue
  }

  Write-Info "Extracting $($item.name) -> $dest"
  New-Item -ItemType Directory -Force -Path $dest | Out-Null
  Expand-Archive -LiteralPath $zipPath -DestinationPath $dest -Force

  $sourceName = [System.IO.Path]::GetFileNameWithoutExtension($item.name)
  Write-Info "Registering source $sourceName -> $($item.subsystem)"
  & $registerCmd -Root $Root -Name $sourceName -Path $dest -Subsystem $item.subsystem -Notes $item.notes
  if (-not $?) {
    throw "Registration failed for $sourceName"
  }

  $processed += 1
}

Write-Host "[ARCHIVE-INTAKE] Processed: $processed"
Write-Host "[ARCHIVE-INTAKE] Skipped: $skipped"
