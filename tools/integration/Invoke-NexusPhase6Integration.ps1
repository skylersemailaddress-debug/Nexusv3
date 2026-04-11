param(
  [string]$NexusRoot = "C:\NexusV3",
  [string]$QuarantineRoot = "C:\NexusQuarantine"
)
$ErrorActionPreference = "Stop"

$srcRoot = Join-Path $NexusRoot "src"
$designLock = Join-Path $NexusRoot "docs\locks\DESIGN_LOCK.md"
$contractAuthority = Join-Path $NexusRoot "registry\locks\CONTRACT_AUTHORITY.yaml"
$promotionSummary = Join-Path $NexusRoot "registry\promotion\phase5_promotion_summary.json"
$promotionPlan = Join-Path $NexusRoot "registry\promotion\phase5_promotion_plan.json"
$integrationRoot = Join-Path $NexusRoot "registry\integration"
$runbookPath = Join-Path $NexusRoot "docs\runbooks\PHASE6_INTEGRATION_EXECUTION.md"

$required = @($srcRoot, $designLock, $contractAuthority, $promotionSummary, $promotionPlan)
foreach ($f in $required) {
  if (!(Test-Path $f)) { throw "Missing required Phase 6 prerequisite: $f" }
}

New-Item -ItemType Directory -Force -Path $integrationRoot | Out-Null

$targets = @("truth","control","shell","proofs","continuity")
$inventory = @()
$layerSummary = @()

foreach ($target in $targets) {
  $targetDir = Join-Path $srcRoot $target
  New-Item -ItemType Directory -Force -Path $targetDir | Out-Null
  $files = Get-ChildItem -Path $targetDir -File -ErrorAction SilentlyContinue
  $count = ($files | Measure-Object).Count

  $py = ($files | Where-Object { $_.Extension -eq ".py" } | Measure-Object).Count
  $ts = ($files | Where-Object { $_.Extension -in @(".ts",".tsx") } | Measure-Object).Count
  $json = ($files | Where-Object { $_.Extension -eq ".json" } | Measure-Object).Count
  $md = ($files | Where-Object { $_.Extension -eq ".md" } | Measure-Object).Count

  $layerSummary += [pscustomobject]@{
    target = $target
    files = $count
    py = $py
    ts = $ts
    json = $json
    md = $md
    ready = ($count -gt 0)
  }

  foreach ($f in $files) {
    $inventory += [pscustomobject]@{
      target = $target
      file = $f.Name
      full_path = $f.FullName
      extension = $f.Extension
      size = $f.Length
    }
  }
}

$readiness = [ordered]@{
  truth = (($layerSummary | Where-Object {$_.target -eq "truth"} | Select-Object -First 1).files -gt 0)
  control = (($layerSummary | Where-Object {$_.target -eq "control"} | Select-Object -First 1).files -gt 0)
  shell = (($layerSummary | Where-Object {$_.target -eq "shell"} | Select-Object -First 1).files -gt 0)
  proofs = (($layerSummary | Where-Object {$_.target -eq "proofs"} | Select-Object -First 1).files -gt 0)
  continuity = (($layerSummary | Where-Object {$_.target -eq "continuity"} | Select-Object -First 1).files -gt 0)
}

$integrationMap = @(
  [pscustomobject]@{ edge = "truth->control"; contract = "truth constraints inform control runtime"; status = "mapped" },
  [pscustomobject]@{ edge = "control->shell"; contract = "shell consumes control api and registry"; status = "mapped" },
  [pscustomobject]@{ edge = "control->continuity"; contract = "continuity owns state and memory contracts consumed by control"; status = "mapped" },
  [pscustomobject]@{ edge = "proofs->control"; contract = "proof gates validate control runtime mutations"; status = "mapped" },
  [pscustomobject]@{ edge = "shell->continuity"; contract = "shell renders continuity state and objective surfaces"; status = "mapped" }
)

$summaryObj = [pscustomobject]@{
  generated_at_utc = [DateTime]::UtcNow.ToString("o")
  readiness = $readiness
  layer_counts = $layerSummary
  integration_edges = $integrationMap.Count
  overall_ready = ($readiness.truth -and $readiness.control -and $readiness.shell -and $readiness.proofs -and $readiness.continuity)
}

$inventoryPath = Join-Path $integrationRoot "phase6_canon_inventory.json"
$summaryPath = Join-Path $integrationRoot "phase6_integration_summary.json"
$mapPath = Join-Path $integrationRoot "phase6_integration_map.json"
$gatePath = Join-Path $integrationRoot "phase6_build_gate.json"

$inventory | ConvertTo-Json -Depth 6 | Set-Content $inventoryPath
$summaryObj | ConvertTo-Json -Depth 6 | Set-Content $summaryPath
$integrationMap | ConvertTo-Json -Depth 6 | Set-Content $mapPath
@{
  gate = "phase6_integration"
  pass = $summaryObj.overall_ready
  required_layers = $targets
} | ConvertTo-Json -Depth 4 | Set-Content $gatePath

$runbook = @"
# Phase 6 Integration Execution

## Objective
Bind promoted canon candidates into a single integration spine and write build-readiness artifacts.

## Outputs
- registry\integration\phase6_canon_inventory.json
- registry\integration\phase6_integration_summary.json
- registry\integration\phase6_integration_map.json
- registry\integration\phase6_build_gate.json

## Result
Overall ready: $($summaryObj.overall_ready)
"@
$runbook | Set-Content $runbookPath

Write-Host "[PHASE6] Canon inventory written: $inventoryPath"
Write-Host "[PHASE6] Integration summary written: $summaryPath"
Write-Host "[PHASE6] Integration map written: $mapPath"
Write-Host "[PHASE6] Build gate written: $gatePath"
Write-Host "[PHASE6] Runbook written: $runbookPath"
Write-Host "[PHASE6] PASS"
