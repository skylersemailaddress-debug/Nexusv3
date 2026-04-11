param(
  [string]$NexusRoot = 'C:\NexusV3',
  [string]$QuarantineRoot = 'C:\NexusQuarantine'
)
$ErrorActionPreference = 'Stop'
$selectionPath = Join-Path $NexusRoot 'registry\planning\phase2_selection_plan.json'
$inventoryPath = Join-Path $QuarantineRoot 'manifests\archive_inventory_summary.json'
if (-not (Test-Path $selectionPath)) { throw "Missing Phase 2 selection plan: $selectionPath" }
if (-not (Test-Path $inventoryPath)) { throw "Missing archive inventory summary: $inventoryPath" }
$selection = Get-Content $selectionPath -Raw | ConvertFrom-Json
$inventory = Get-Content $inventoryPath -Raw | ConvertFrom-Json
$canonDirs = @(
  (Join-Path $NexusRoot 'src\truth'),
  (Join-Path $NexusRoot 'src\control'),
  (Join-Path $NexusRoot 'src\shell'),
  (Join-Path $NexusRoot 'src\proofs'),
  (Join-Path $NexusRoot 'src\continuity'),
  (Join-Path $NexusRoot 'registry\extraction')
)
$canonDirs | ForEach-Object { New-Item -ItemType Directory -Force -Path $_ | Out-Null }
$roleMap = @{
  'truth_gap_methodology' = 'truth'
  'integrated_control_plane_skeleton' = 'control'
  'conversation_shell_and_blocks' = 'shell'
  'assembly_and_release_proofs' = 'proofs'
  'continuity_and_operator_os' = 'continuity'
}
$plan = @()
$normalization = @()
$conflicts = @()
foreach ($item in $selection) {
  $role = [string]$item.canon_role
  if (-not $roleMap.ContainsKey($role)) { continue }
  $target = $roleMap[$role]
  $archive = $inventory.archives | Where-Object { $_.file -eq $item.recommended_primary } | Select-Object -First 1
  if (-not $archive) { continue }
  $record = [ordered]@{
    family = [string]$item.family
    canon_role = $role
    target = $target
    source_archive = [string]$archive.file
    source_expanded_path = [string]$archive.expanded_path
    extraction_mode = 'subsystem_extract_only'
    whole_repo_merge = $false
    status = 'planned'
  }
  $plan += [pscustomobject]$record
  $stub = @"
# Phase 3 extraction stub
family: $($item.family)
canon_role: $role
target: $target
source_archive: $($archive.file)
source_expanded_path: $($archive.expanded_path)
mode: subsystem_extract_only
notes:
- no whole-repo merge
- normalize contracts before promotion
- preserve alternates in quarantine
"@
  $stubPath = Join-Path $NexusRoot ("src\{0}\EXTRACTION_STUB_{1}.md" -f $target, ([string]$item.family).Replace(' ','_'))
  Set-Content -Path $stubPath -Value $stub -Encoding UTF8
}
$normalization += [pscustomobject]@{ concern='auth'; action='unify_before_promotion'; authority='single_contract_required' }
$normalization += [pscustomobject]@{ concern='state'; action='unify_before_promotion'; authority='single_runtime_truth' }
$normalization += [pscustomobject]@{ concern='execution_graph'; action='unify_before_promotion'; authority='single_execution_graph_root' }
$normalization += [pscustomobject]@{ concern='memory_schema'; action='normalize_before_promotion'; authority='tiered_memory_contract' }
$conflicts += [pscustomobject]@{ family='Nexus2.9'; conflict='duplicate_control_plane_variants'; primary='Nexus2.9 (10).zip'; alternate='Nexus2.9 (9).zip'; resolution='primary_locked_alternate_quarantined' }
$conflicts += [pscustomobject]@{ family='SkyGPTAgent'; conflict='duplicate_continuity_variants'; primary='SkyGPTAgent (2).zip'; alternate='SkyGPTAgent (32).zip'; resolution='primary_locked_alternate_quarantined' }
$conflicts += [pscustomobject]@{ family='ODP'; conflict='multiple_proof_variants'; primary='ODP_clean (4).zip'; alternate='ODP_FACTORY (3).zip, ODPv2.zip, ODPv3_CAPTURE.zip'; resolution='primary_locked_alternates_reference_only' }
$plan | ConvertTo-Json -Depth 6 | Set-Content (Join-Path $NexusRoot 'registry\extraction\phase3_extraction_plan.json') -Encoding UTF8
$normalization | ConvertTo-Json -Depth 6 | Set-Content (Join-Path $NexusRoot 'registry\extraction\phase3_normalization_map.json') -Encoding UTF8
$conflicts | ConvertTo-Json -Depth 6 | Set-Content (Join-Path $NexusRoot 'registry\extraction\phase3_conflict_register.json') -Encoding UTF8
$md = @()
$md += '# Phase 3 Canon Assembly Plan'
$md += ''
$md += '## Objective'
$md += 'Create the first canon tree from Phase 2 winners without whole-repo merges.'
$md += ''
$md += '## Targets'
foreach ($p in $plan) { $md += "- $($p.target) <= $($p.source_archive) [$($p.family)]" }
$md += ''
$md += '## Normalization requirements'
foreach ($n in $normalization) { $md += "- $($n.concern): $($n.action) ($($n.authority))" }
$md += ''
$md += '## Active conflicts'
foreach ($c in $conflicts) { $md += "- $($c.family): $($c.conflict) :: $($c.resolution)" }
$md += ''
$md += '## Deliverables'
$md += '- phase3_extraction_plan.json'
$md += '- phase3_normalization_map.json'
$md += '- phase3_conflict_register.json'
$md += '- extraction stubs under src\*'
Set-Content -Path (Join-Path $NexusRoot 'docs\runbooks\PHASE3_CANON_ASSEMBLY_PLAN.md') -Value ($md -join [Environment]::NewLine) -Encoding UTF8
Write-Host "[PHASE3] Extraction plan written: $(Join-Path $NexusRoot 'registry\extraction\phase3_extraction_plan.json')"
Write-Host "[PHASE3] Normalization map written: $(Join-Path $NexusRoot 'registry\extraction\phase3_normalization_map.json')"
Write-Host "[PHASE3] Conflict register written: $(Join-Path $NexusRoot 'registry\extraction\phase3_conflict_register.json')"
Write-Host "[PHASE3] Canon assembly plan written: $(Join-Path $NexusRoot 'docs\runbooks\PHASE3_CANON_ASSEMBLY_PLAN.md')"
Write-Host '[PHASE3] PASS'
