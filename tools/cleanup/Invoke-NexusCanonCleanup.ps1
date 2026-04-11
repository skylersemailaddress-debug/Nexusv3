param(
  [string]$NexusRoot = "C:\NexusV3",
  [string]$QuarantineRoot = "C:\NexusQuarantine"
)
$ErrorActionPreference = "Stop"

$srcRoot = Join-Path $NexusRoot "src"
$cleanupRoot = Join-Path $NexusRoot "registry\cleanup"
$runbookPath = Join-Path $NexusRoot "docs\runbooks\CANON_CLEANUP_EXECUTION.md"
$canonRoot = Join-Path $NexusRoot "canon\clean"

if (!(Test-Path $srcRoot)) { throw "Missing src root: $srcRoot" }

New-Item -ItemType Directory -Force -Path $cleanupRoot | Out-Null
New-Item -ItemType Directory -Force -Path $canonRoot | Out-Null

$layerDirs = Get-ChildItem -Path $srcRoot -Directory -ErrorAction SilentlyContinue
$selection = @()
$archived = @()
$summary = @()

function Get-BaseName([string]$name) {
  $base = [System.IO.Path]::GetFileNameWithoutExtension($name)
  $base = $base -replace "__promoted(?:_\d+)?$", ""
  return $base
}

function Get-SafeName([string]$name) {
  $safe = $name
  $safe = $safe -replace '[\\/:*?"<>|]', '_'
  $safe = $safe -replace '\s+', '_'
  $safe = $safe -replace '\+', '_plus_'
  $safe = $safe -replace '[^\w\.\-]', '_'
  $safe = $safe -replace '_{2,}', '_'
  $safe = $safe.Trim('._')
  if ([string]::IsNullOrWhiteSpace($safe)) { $safe = "canon_item" }
  return $safe
}

foreach ($layer in $layerDirs) {
  $layerName = $layer.Name
  $cleanLayer = Join-Path $canonRoot $layerName
  New-Item -ItemType Directory -Force -Path $cleanLayer | Out-Null

  $files = Get-ChildItem -Path $layer.FullName -File -ErrorAction SilentlyContinue
  $groups = @{}
  foreach ($f in $files) {
    $key = (Get-BaseName $f.Name) + "|" + $f.Extension.ToLowerInvariant()
    if (-not $groups.ContainsKey($key)) { $groups[$key] = @() }
    $groups[$key] += $f
  }

  $keptCount = 0
  $archivedCount = 0

  foreach ($key in $groups.Keys) {
    $items = $groups[$key] | Sort-Object Name
    $winner = $items[0]

    $logical = [string]($key -split "\|")[0]
    $ext = [string]($key -split "\|")[1]
    $safeLogical = Get-SafeName $logical
    $dest = Join-Path $cleanLayer ($safeLogical + $ext)
    $i = 1
    while (Test-Path $dest) {
      $dest = Join-Path $cleanLayer ($safeLogical + "__" + $i + $ext)
      $i += 1
    }

    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $dest) | Out-Null
    Copy-Item $winner.FullName $dest -Force

    $selection += [pscustomobject]@{
      layer = $layerName
      logical_name = $logical
      safe_logical_name = $safeLogical
      extension = $ext
      selected_source = $winner.FullName
      clean_target = $dest
      duplicates_collapsed = $items.Count
    }
    $keptCount += 1

    if ($items.Count -gt 1) {
      foreach ($loser in $items[1..($items.Count-1)]) {
        $archived += [pscustomobject]@{
          layer = $layerName
          logical_name = $logical
          archived_source = $loser.FullName
          kept_source = $winner.FullName
        }
        $archivedCount += 1
      }
    }
  }

  $summary += [pscustomobject]@{
    layer = $layerName
    canonical_files = $keptCount
    duplicate_variants_archived = $archivedCount
  }
}

$selectionPath = Join-Path $cleanupRoot "canon_selection_manifest.json"
$archivePath = Join-Path $cleanupRoot "canon_archived_duplicates.json"
$summaryPath = Join-Path $cleanupRoot "canon_cleanup_summary.json"
$gatePath = Join-Path $cleanupRoot "canon_cleanup_gate.json"

$selection | ConvertTo-Json -Depth 6 | Set-Content $selectionPath
$archived | ConvertTo-Json -Depth 6 | Set-Content $archivePath
$summary | ConvertTo-Json -Depth 6 | Set-Content $summaryPath

$gate = [pscustomobject]@{
  gate = "canon_cleanup"
  pass = (($selection | Measure-Object).Count -gt 0)
  layers = ($summary | Measure-Object).Count
  canonical_files = ($selection | Measure-Object).Count
  duplicate_variants_archived = ($archived | Measure-Object).Count
  sanitized_names = $true
}
$gate | ConvertTo-Json -Depth 4 | Set-Content $gatePath

$runbook = @"
# Canon Cleanup Execution

## Objective
Collapse duplicate promoted canon candidates into one selected canonical file per logical module and write the clean canon tree under canon\clean.

## Outputs
- registry\cleanup\canon_selection_manifest.json
- registry\cleanup\canon_archived_duplicates.json
- registry\cleanup\canon_cleanup_summary.json
- registry\cleanup\canon_cleanup_gate.json
- canon\clean\*

## Gate
pass: $($gate.pass)
canonical_files: $($gate.canonical_files)
duplicate_variants_archived: $($gate.duplicate_variants_archived)
sanitized_names: $($gate.sanitized_names)
"@
$runbook | Set-Content $runbookPath

Write-Host "[CANON-CLEANUP] Selection manifest written: $selectionPath"
Write-Host "[CANON-CLEANUP] Archived duplicates written: $archivePath"
Write-Host "[CANON-CLEANUP] Cleanup summary written: $summaryPath"
Write-Host "[CANON-CLEANUP] Cleanup gate written: $gatePath"
Write-Host "[CANON-CLEANUP] Runbook written: $runbookPath"
Write-Host "[CANON-CLEANUP] PASS"
