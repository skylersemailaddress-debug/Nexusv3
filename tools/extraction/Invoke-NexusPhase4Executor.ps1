param(
  [string]$NexusRoot = "C:\NexusV3",
  [string]$QuarantineRoot = "C:\NexusQuarantine"
)
$ErrorActionPreference = "Stop"

$phase3Plan = Join-Path $NexusRoot "registry\extraction\phase3_extraction_plan.json"
if (!(Test-Path $phase3Plan)) { throw "Missing phase3 plan: $phase3Plan" }

$phase3 = Get-Content $phase3Plan -Raw | ConvertFrom-Json

$stagingRoot = Join-Path $NexusRoot "staging\phase4"
$registryRoot = Join-Path $NexusRoot "registry\phase4"
$runbookPath = Join-Path $NexusRoot "docs\runbooks\PHASE4_EXECUTION_PLAN.md"

New-Item -ItemType Directory -Force -Path $stagingRoot | Out-Null
New-Item -ItemType Directory -Force -Path $registryRoot | Out-Null

$summary = @()
$manifest = @()

function Test-MeaningfulPath {
  param([string]$FullName, [string]$Target)

  $p = $FullName.ToLowerInvariant()
  $n = [System.IO.Path]::GetFileName($FullName).ToLowerInvariant()

  if ($p -match "\\\.git\\") { return $false }
  if ($p -match "\\\.venv\\") { return $false }
  if ($p -match "\\node_modules\\") { return $false }
  if ($p -match "\\__pycache__\\") { return $false }
  if ($p -match "\\dist-info\\") { return $false }
  if ($p -match "\\site-packages\\") { return $false }
  if ($p -match "\\vendor\\") { return $false }
  if ($p -match "\\generated\\") { return $false }
  if ($p -match "\\quarantine\\") { return $false }
  if ($p -match "\\_archive\\") { return $false }
  if ($p -match "\\archive\\") { return $false }

  if ($n -match "^log(\.old)?$") { return $false }
  if ($n -match "^lock$") { return $false }
  if ($n -match "^requested$") { return $false }
  if ($n -match "\.py\.typed$") { return $false }
  if ($n -match "\.gitkeep$") { return $false }
  if ($n -match "\.journal$") { return $false }
  if ($n -match "\.wal$") { return $false }
  if ($n -match "\.db$") { return $false }
  if ($n -match "\.sqlite") { return $false }
  if ($n -match "\.map$") { return $false }
  if ($n -match "\.min\.js$") { return $false }
  if ($n -match "\.d\.ts$") { return $false }

  $ext = [System.IO.Path]::GetExtension($n)
  if ($ext -notin @(".py",".ts",".tsx",".js",".jsx",".json",".yaml",".yml",".md",".sql",".toml")) { return $false }

  switch ($Target) {
    "truth" {
      return ($p -match "truth|invariant|contract|gap|canon|doctrine|decision|schema")
    }
    "control" {
      return ($p -match "apps\\api|routes|services|models|adapters|registry|runtime|control|health|auth|worker|runner")
    }
    "shell" {
      return ($p -match "apps\\web|components|shell|blocks|ui|page|layout|composer")
    }
    "proofs" {
      return ($p -match "proof|gate|assembly|release|audit|validator|manifest|check")
    }
    "continuity" {
      return ($p -match "memory|state|checkpoint|objective|resume|context|continuity|trace|queue|workflow")
    }
    default { return $false }
  }
}

foreach ($entry in $phase3) {
  $src = [string]$entry.source_expanded_path
  if (!(Test-Path $src)) { continue }

  $family = [string]$entry.family
  $target = [string]$entry.target
  $targetRoot = Join-Path $stagingRoot $target
  $familyRoot = Join-Path $targetRoot $family
  New-Item -ItemType Directory -Force -Path $familyRoot | Out-Null

  $files = Get-ChildItem -Path $src -Recurse -File -ErrorAction SilentlyContinue |
    Where-Object { $_.Length -lt 1048576 } |
    Where-Object { Test-MeaningfulPath -FullName $_.FullName -Target $target } |
    Sort-Object FullName

  $count = 0
  foreach ($f in $files) {
    if ($count -ge 40) { break }
    $dest = Join-Path $familyRoot $f.Name
    $base = [System.IO.Path]::GetFileNameWithoutExtension($f.Name)
    $ext = [System.IO.Path]::GetExtension($f.Name)
    $i = 1
    while (Test-Path $dest) {
      $dest = Join-Path $familyRoot ($base + "__" + $i + $ext)
      $i += 1
    }
    Copy-Item $f.FullName $dest -Force
    $manifest += [pscustomobject]@{
      family = $family
      target = $target
      source_archive = [string]$entry.source_archive
      source_file = $f.FullName
      staged_file = $dest
      status = "staged_semantic"
    }
    $count++
  }

  $summary += [pscustomobject]@{
    family = $family
    target = $target
    source_archive = [string]$entry.source_archive
    staged = $count
  }
}

$summaryPath = Join-Path $registryRoot "phase4_execution_summary.json"
$manifestPath = Join-Path $registryRoot "phase4_promotion_manifest.json"
$summary | ConvertTo-Json -Depth 5 | Set-Content $summaryPath
$manifest | ConvertTo-Json -Depth 5 | Set-Content $manifestPath

$runbook = @"
# Phase 4 Execution Plan

## Objective
Stage semantically meaningful candidate files from locked primaries and allowed references into canon staging without whole-repo merges.

## Filters enforced
- excludes: .git, .venv, node_modules, site-packages, dist-info, generated, quarantine, archive
- excludes: LOCK, LOG, REQUESTED, .py.typed, .gitkeep, .journal, .wal, .db, .d.ts
- includes only target-relevant paths by layer semantics

## Outputs
- registry\phase4\phase4_execution_summary.json
- registry\phase4\phase4_promotion_manifest.json
- staging\phase4\*

## Rule
No staged file is canon authority until explicit promotion.
"@
$runbook | Set-Content $runbookPath

Write-Host "[PHASE4] Execution summary written: $summaryPath"
Write-Host "[PHASE4] Promotion manifest written: $manifestPath"
Write-Host "[PHASE4] Runbook written: $runbookPath"
Write-Host "[PHASE4] PASS"
