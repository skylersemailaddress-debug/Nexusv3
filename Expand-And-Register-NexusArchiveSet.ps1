param(
  [string]$SourceRoot = 'C:\NexusArchiveDrop',
  [string]$NexusRoot = 'C:\NexusV3',
  [string]$QuarantineRoot = 'C:\NexusQuarantine',
  [switch]$ExpandAll,
  [switch]$NoExpand,
  [string[]]$IncludeNames
)
$ErrorActionPreference = 'Stop'
function Write-Log($m){ Write-Host "[ARCHIVE-EXPANSION] $m" }
function Ensure-Dir([string]$p){ New-Item -ItemType Directory -Force -Path $p | Out-Null }
function Get-Sha256([string]$p){ (Get-FileHash -Algorithm SHA256 -LiteralPath $p).Hash.ToLower() }

$knownPath = "$NexusRoot\registry\sources\KNOWN_ARCHIVES_V2.json"
if (-not (Test-Path $knownPath)) { throw "Missing known archive registry: $knownPath" }
$known = Get-Content $knownPath -Raw | ConvertFrom-Json

$dirs = @(
  "$QuarantineRoot\archives",
  "$QuarantineRoot\expanded",
  "$QuarantineRoot\manifests",
  "$QuarantineRoot\fingerprints",
  "$QuarantineRoot\logs"
)
$dirs | ForEach-Object { Ensure-Dir $_ }

$records = @()
$seenByHash = @{}
$processed = 0
$expanded = 0
$skipped = 0

foreach ($entry in $known.archives) {
  if ($IncludeNames -and ($IncludeNames -notcontains [string]$entry.file)) { continue }
  $src = Join-Path $SourceRoot $entry.file
  if (-not (Test-Path $src)) {
    Write-Log "Skipping missing archive: $($entry.file)"
    $skipped++
    continue
  }
  $sha = Get-Sha256 $src
  $size = (Get-Item $src).Length
  $safe = ($entry.slug -replace '[^A-Za-z0-9._-]', '_')
  $archiveTarget = Join-Path "$QuarantineRoot\archives" $entry.file
  if (-not (Test-Path $archiveTarget)) { Copy-Item -LiteralPath $src -Destination $archiveTarget -Force }

  $expandPath = Join-Path "$QuarantineRoot\expanded" $safe
  $duplicateOf = $null
  if ($seenByHash.ContainsKey($sha)) { $duplicateOf = $seenByHash[$sha] } else { $seenByHash[$sha] = $entry.file }

  $shouldExpand = $false
  if (-not $NoExpand) {
    if ($ExpandAll) { $shouldExpand = $true }
    elseif (-not $duplicateOf) { $shouldExpand = $true }
  }

  if ($shouldExpand) {
    if (Test-Path $expandPath) { Remove-Item -LiteralPath $expandPath -Recurse -Force }
    Ensure-Dir $expandPath
    Expand-Archive -LiteralPath $archiveTarget -DestinationPath $expandPath -Force
    $expanded++
  }

  $top = @()
  if (Test-Path $expandPath) {
    $top = Get-ChildItem -LiteralPath $expandPath | Select-Object -ExpandProperty Name
  }
  $record = [ordered]@{
    file = [string]$entry.file
    slug = [string]$entry.slug
    family = [string]$entry.family
    canon_role = [string]$entry.canon_role
    source_path = $src
    quarantine_archive = $archiveTarget
    expanded_path = $expandPath
    sha256 = $sha
    size_bytes = $size
    duplicate_of = $duplicateOf
    expanded = [bool]$shouldExpand
    top_level_items = $top
    processed_at_utc = [DateTime]::UtcNow.ToString('o')
  }
  $records += [pscustomobject]$record
  $manifestPath = Join-Path "$QuarantineRoot\manifests" ($safe + '.manifest.json')
  $record | ConvertTo-Json -Depth 8 | Set-Content $manifestPath -Encoding utf8
  $processed++
}

$summary = [ordered]@{
  processed = $processed
  expanded = $expanded
  skipped = $skipped
  generated_at_utc = [DateTime]::UtcNow.ToString('o')
  archives = $records
}
$summary | ConvertTo-Json -Depth 8 | Set-Content "$QuarantineRoot\manifests\archive_inventory_summary.json" -Encoding utf8
$records | Export-Csv "$QuarantineRoot\manifests\archive_inventory_summary.csv" -NoTypeInformation -Encoding utf8
$records | ForEach-Object {
  [pscustomobject]@{
    file = $_.file
    sha256 = $_.sha256
    duplicate_of = $_.duplicate_of
    family = $_.family
    canon_role = $_.canon_role
  }
} | Export-Csv "$QuarantineRoot\fingerprints\archive_fingerprints.csv" -NoTypeInformation -Encoding utf8

Write-Log "Processed: $processed"
Write-Log "Expanded: $expanded"
Write-Log "Skipped: $skipped"
Write-Log "Summary: $QuarantineRoot\manifests\archive_inventory_summary.json"
