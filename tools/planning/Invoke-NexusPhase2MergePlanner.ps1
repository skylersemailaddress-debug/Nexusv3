param(
  [Parameter(Mandatory=$true)][string]$NexusRoot,
  [Parameter(Mandatory=$true)][string]$QuarantineRoot
)
$ErrorActionPreference = 'Stop'

$inventoryPath = Join-Path $QuarantineRoot 'manifests\archive_inventory_summary.json'
if (-not (Test-Path $inventoryPath)) { throw "Missing inventory: $inventoryPath" }
$inventory = Get-Content $inventoryPath -Raw | ConvertFrom-Json
$archives = @($inventory.archives)
if ($archives.Count -eq 0) { throw 'No archives found in inventory summary.' }

function Get-Score([object]$a) {
  $score = 0
  switch ($a.family) {
    'Nexus2.9' { $score += 95 }
    'SkylerOS-Truth' { $score += 94 }
    'FrankV2' { $score += 92 }
    'FrankCore' { $score += 88 }
    'ODP' { $score += 84 }
    'SkylerOS' { $score += 83 }
    'SkyGPTAgent' { $score += 82 }
    'NexusV3' { $score += 80 }
    'Nexus2.8' { $score += 78 }
    'Nexus' { $score += 75 }
    'NexusV2' { $score += 73 }
    'autobuilder2.9' { $score += 77 }
    'autobuilder' { $score += 72 }
    'autobuilderv2' { $score += 70 }
    default { $score += 60 }
  }
  switch ($a.canon_role) {
    'integrated_control_plane_skeleton' { $score += 20 }
    'truth_gap_methodology' { $score += 19 }
    'conversation_shell_and_blocks' { $score += 18 }
    'assembly_and_release_proofs' { $score += 15 }
    'continuity_and_operator_os' { $score += 16 }
    'bootstrap_canon_repo' { $score += 14 }
    'transitional_api_runtime_reference' { $score += 12 }
    'control_pack_doctrine' { $score += 11 }
    default { $score += 5 }
  }
  if ($a.expanded -eq $true) { $score += 5 }
  $sizeMb = [math]::Round(([double]$a.size_bytes / 1MB), 2)
  if ($sizeMb -gt 1 -and $sizeMb -lt 250) { $score += 3 }
  return [int]$score
}

$scored = foreach ($a in $archives) {
  [pscustomobject]@{
    file = $a.file
    family = $a.family
    canon_role = $a.canon_role
    score = Get-Score $a
    size_mb = [math]::Round(([double]$a.size_bytes / 1MB), 2)
    expanded_path = $a.expanded_path
    source_path = $a.source_path
    sha256 = $a.sha256
  }
}

$sorted = $scored | Sort-Object -Property @(
  @{Expression='score'; Descending=$true},
  @{Expression='family'; Descending=$false},
  @{Expression='file'; Descending=$false}
)

$csvPath = Join-Path $NexusRoot 'registry\planning\phase2_repo_scores.csv'
$sorted | Export-Csv -NoTypeInformation -Encoding UTF8 -Path $csvPath

$families = $sorted | Group-Object family
$selection = foreach ($g in $families) {
  $primary = $g.Group | Sort-Object -Property @(
    @{Expression='score'; Descending=$true},
    @{Expression='size_mb'; Descending=$true},
    @{Expression='file'; Descending=$false}
  ) | Select-Object -First 1
  [pscustomobject]@{
    family = $g.Name
    recommended_primary = $primary.file
    canon_role = $primary.canon_role
    score = $primary.score
    alternates = @($g.Group | Where-Object { $_.file -ne $primary.file } | Select-Object -ExpandProperty file)
  }
}

$selectionPath = Join-Path $NexusRoot 'registry\planning\phase2_selection_plan.json'
$selection | ConvertTo-Json -Depth 6 | Set-Content -Encoding UTF8 -Path $selectionPath

$extractBatches = @(
  [pscustomobject]@{ batch='B1'; target='truth'; source_family='SkylerOS-Truth'; purpose='truth docs, gaps, invariants, canon contracts' },
  [pscustomobject]@{ batch='B2'; target='control-plane'; source_family='Nexus2.9'; purpose='admin/control-plane API and runtime skeleton' },
  [pscustomobject]@{ batch='B3'; target='conversation-shell'; source_family='FrankV2'; purpose='operator shell and block UI patterns' },
  [pscustomobject]@{ batch='B4'; target='proofs'; source_family='ODP'; purpose='assembly gates and release proofs' },
  [pscustomobject]@{ batch='B5'; target='continuity'; source_family='SkylerOS'; purpose='continuity, operator OS, stateful memory concepts' }
)
$batchPath = Join-Path $NexusRoot 'registry\planning\phase2_extraction_batches.json'
$extractBatches | ConvertTo-Json -Depth 4 | Set-Content -Encoding UTF8 -Path $batchPath

$mdPath = Join-Path $NexusRoot 'docs\runbooks\PHASE2_MERGE_PLAN.md'
$lines = @()
$lines += '# Phase 2 Merge Plan'
$lines += ''
$lines += '## Objective'
$lines += 'Select one primary source per canon role and preserve alternates for controlled extraction. No whole-repo merges.'
$lines += ''
$lines += '## Recommended primaries by family'
foreach ($item in ($selection | Sort-Object family)) {
  $lines += "- $($item.family): $($item.recommended_primary) [$($item.canon_role)] score=$($item.score)"
}
$lines += ''
$lines += '## Extraction order'
foreach ($b in $extractBatches) {
  $lines += "- $($b.batch): $($b.target) <= $($b.source_family) :: $($b.purpose)"
}
$lines += ''
$lines += '## Deliverables'
$lines += '- phase2_repo_scores.csv'
$lines += '- phase2_selection_plan.json'
$lines += '- phase2_extraction_batches.json'
$lines += '- this merge plan'
Set-Content -Encoding UTF8 -Path $mdPath -Value $lines

Write-Host '[PHASE2] Repo scoring written:' $csvPath
Write-Host '[PHASE2] Selection plan written:' $selectionPath
Write-Host '[PHASE2] Extraction batches written:' $batchPath
Write-Host '[PHASE2] Merge plan written:' $mdPath
Write-Host '[PHASE2] PASS'
