param(
  [string]$NexusRoot = "C:\NexusV3",
  [string]$QuarantineRoot = "C:\NexusQuarantine"
)
$ErrorActionPreference = "Stop"

$stagingRoot = Join-Path $NexusRoot "staging\phase4"
$designLock = Join-Path $NexusRoot "docs\locks\DESIGN_LOCK.md"
$promotionRules = Join-Path $NexusRoot "docs\locks\PROMOTION_RULES.md"
$outRoot = Join-Path $NexusRoot "registry\promotion"
$srcRoot = Join-Path $NexusRoot "src"

$required = @($stagingRoot, $designLock, $promotionRules)
foreach ($f in $required) {
  if (!(Test-Path $f)) { throw "Missing required Phase 5 prerequisite: $f" }
}

New-Item -ItemType Directory -Force -Path $outRoot | Out-Null
$targets = @("truth","control","shell","proofs","continuity")
foreach ($t in $targets) {
  New-Item -ItemType Directory -Force -Path (Join-Path $srcRoot $t) | Out-Null
}

$familyPriority = @{
  "SkylerOS-Truth" = 100
  "Nexus2.9" = 95
  "FrankV2" = 95
  "ODP" = 90
  "SkylerOS" = 92
  "autobuilder2.9" = 80
  "FrankCore" = 75
  "SkyGPTAgent" = 70
  "SkylerGPTOS" = 65
  "SkyOSsplitoff" = 40
  "SkyOS" = 0
}

function Get-Score([string]$family,[string]$full,[string]$name) {
  $score = 0
  if ($familyPriority.ContainsKey($family)) { $score += $familyPriority[$family] }
  $lname = $name.ToLowerInvariant()
  $lfull = $full.ToLowerInvariant()
  if ($lname -match "main|auth|db|registry|state|memory|resume|checkpoint|composer|appshell|layout|page|proof|manifest|schema") { $score += 20 }
  if ($lfull -match "routes|services|models|components|stores|contracts|workflows|schemas|truth") { $score += 15 }
  if ($lname -match "__init__") { $score -= 10 }
  if ($lname -match "test_") { $score -= 8 }
  if ($lname -match "package-lock") { $score -= 6 }
  return $score
}

$scored = @()
foreach ($target in $targets) {
  $targetRoot = Join-Path $stagingRoot $target
  if (!(Test-Path $targetRoot)) { continue }
  $familyDirs = Get-ChildItem -Path $targetRoot -Directory -ErrorAction SilentlyContinue
  foreach ($fd in $familyDirs) {
    $family = $fd.Name
    $files = Get-ChildItem -Path $fd.FullName -File -ErrorAction SilentlyContinue
    foreach ($f in $files) {
      $score = Get-Score -family $family -full $f.FullName -name $f.Name
      $scored += [pscustomobject]@{
        family = $family
        target = $target
        staged_file = $f.FullName
        file_name = $f.Name
        score = $score
      }
    }
  }
}

$selected = @()
$grouped = $scored | Group-Object target
foreach ($g in $grouped) {
  $ordered = $g.Group | Sort-Object @{Expression='score';Descending=$true}, @{Expression='family';Descending=$false}, @{Expression='file_name';Descending=$false}
  $count = 0
  foreach ($item in $ordered) {
    if ($count -ge 15) { break }
    if (!(Test-Path $item.staged_file)) { continue }
    $selected += $item
    $count++
  }
}

$promotionPlan = @()
$promotionActions = @()
foreach ($item in $selected) {
  $targetDir = Join-Path $srcRoot $item.target
  $base = [System.IO.Path]::GetFileNameWithoutExtension($item.file_name)
  $ext = [System.IO.Path]::GetExtension($item.file_name)
  $dest = Join-Path $targetDir ($base + "__promoted" + $ext)
  $i = 1
  while (Test-Path $dest) {
    $dest = Join-Path $targetDir ($base + "__promoted_" + $i + $ext)
    $i += 1
  }
  Copy-Item $item.staged_file $dest -Force
  $promotionPlan += [pscustomobject]@{
    target = $item.target
    family = $item.family
    staged_file = $item.staged_file
    promoted_file = $dest
    score = $item.score
    status = "promoted_candidate"
  }
  $promotionActions += [pscustomobject]@{
    action = "copy_to_canon_candidate"
    target = $item.target
    from = $item.staged_file
    to = $dest
    score = $item.score
  }
}

$summary = $promotionPlan | Group-Object target | ForEach-Object {
  [pscustomobject]@{
    target = $_.Name
    promoted = $_.Count
    top_family = ($_.Group | Sort-Object @{Expression='score';Descending=$true} | Select-Object -First 1).family
  }
}

$planPath = Join-Path $outRoot "phase5_promotion_plan.json"
$actionsPath = Join-Path $outRoot "phase5_promotion_actions.json"
$summaryPath = Join-Path $outRoot "phase5_promotion_summary.json"
$runbookPath = Join-Path $NexusRoot "docs\runbooks\PHASE5_PROMOTION_EXECUTION.md"

$promotionPlan | ConvertTo-Json -Depth 6 | Set-Content $planPath
$promotionActions | ConvertTo-Json -Depth 6 | Set-Content $actionsPath
$summary | ConvertTo-Json -Depth 6 | Set-Content $summaryPath

$runbook = @"
# Phase 5 Promotion Execution

## Objective
Promote top-scored currently staged candidates into canon candidate slots under src\* without whole-repo merges.

## Outputs
- registry\promotion\phase5_promotion_plan.json
- registry\promotion\phase5_promotion_actions.json
- registry\promotion\phase5_promotion_summary.json

## Rule
This version reads the current staging tree directly and does not trust stale manifest paths.
"@
$runbook | Set-Content $runbookPath

Write-Host "[PHASE5] Promotion plan written: $planPath"
Write-Host "[PHASE5] Promotion actions written: $actionsPath"
Write-Host "[PHASE5] Promotion summary written: $summaryPath"
Write-Host "[PHASE5] Runbook written: $runbookPath"
Write-Host "[PHASE5] PASS"
