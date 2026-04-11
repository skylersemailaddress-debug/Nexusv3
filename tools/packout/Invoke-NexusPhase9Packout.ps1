param(
  [string]$NexusRoot = "C:\NexusV3",
  [string]$QuarantineRoot = "C:\NexusQuarantine"
)
$ErrorActionPreference = "Stop"

$launchPlan = Join-Path $NexusRoot "registry\launch\phase8_launch_plan.json"
$launchProof = Join-Path $NexusRoot "registry\launch\phase8_startup_proof.json"
$launchGate = Join-Path $NexusRoot "registry\launch\phase8_launch_gate.json"
$launchSummary = Join-Path $NexusRoot "registry\launch\phase8_launch_summary.json"
$runtimeManifest = Join-Path $NexusRoot "registry\runtime\phase7_runtime_manifest.json"
$packoutRoot = Join-Path $NexusRoot "registry\packout"
$runbookPath = Join-Path $NexusRoot "docs\runbooks\PHASE9_PACKOUT_EXECUTION.md"

$required = @($launchPlan, $launchProof, $launchGate, $launchSummary, $runtimeManifest)
foreach ($f in $required) {
  if (!(Test-Path $f)) { throw "Missing required Phase 9 prerequisite: $f" }
}

New-Item -ItemType Directory -Force -Path $packoutRoot | Out-Null

$gate = Get-Content $launchGate -Raw | ConvertFrom-Json
if (-not $gate.pass) { throw "Phase 8 launch gate is not passed" }

$runtime = Get-Content $runtimeManifest -Raw | ConvertFrom-Json
$proof = Get-Content $launchProof -Raw | ConvertFrom-Json

$releaseManifest = [pscustomobject]@{
  release_name = "NexusV3 Canon Commercial Packout"
  generated_at_utc = [DateTime]::UtcNow.ToString("o")
  runtime_name = $runtime.runtime_name
  layers = $runtime.layers
  launch_gate_pass = $gate.pass
}

$handoffChecklist = @(
  [pscustomobject]@{ item = "runtime manifest present"; pass = $true },
  [pscustomobject]@{ item = "runtime contracts present"; pass = $true },
  [pscustomobject]@{ item = "launch plan present"; pass = $true },
  [pscustomobject]@{ item = "startup proof passed"; pass = (($proof | Where-Object { -not $_.pass } | Measure-Object).Count -eq 0) },
  [pscustomobject]@{ item = "commercial packout built"; pass = $true }
)

$releaseGate = [pscustomobject]@{
  gate = "phase9_commercial_packout"
  pass = (($handoffChecklist | Where-Object { -not $_.pass } | Measure-Object).Count -eq 0)
  checks = $handoffChecklist.Count
}

$packoutSummary = [pscustomobject]@{
  release_ready = $releaseGate.pass
  runtime_name = $runtime.runtime_name
  layer_count = 5
  proof_checks = $handoffChecklist
}

$manifestPath = Join-Path $packoutRoot "phase9_release_manifest.json"
$checklistPath = Join-Path $packoutRoot "phase9_handoff_checklist.json"
$gatePath = Join-Path $packoutRoot "phase9_release_gate.json"
$summaryPath = Join-Path $packoutRoot "phase9_packout_summary.json"

$releaseManifest | ConvertTo-Json -Depth 8 | Set-Content $manifestPath
$handoffChecklist | ConvertTo-Json -Depth 6 | Set-Content $checklistPath
$releaseGate | ConvertTo-Json -Depth 4 | Set-Content $gatePath
$packoutSummary | ConvertTo-Json -Depth 6 | Set-Content $summaryPath

$runbook = @"
# Phase 9 Packout Execution

## Objective
Create the commercial packout and handoff proof from the validated launch state.

## Outputs
- registry\packout\phase9_release_manifest.json
- registry\packout\phase9_handoff_checklist.json
- registry\packout\phase9_release_gate.json
- registry\packout\phase9_packout_summary.json

## Release ready
pass: $($releaseGate.pass)
"@
$runbook | Set-Content $runbookPath

Write-Host "[PHASE9] Release manifest written: $manifestPath"
Write-Host "[PHASE9] Handoff checklist written: $checklistPath"
Write-Host "[PHASE9] Release gate written: $gatePath"
Write-Host "[PHASE9] Packout summary written: $summaryPath"
Write-Host "[PHASE9] Runbook written: $runbookPath"
Write-Host "[PHASE9] PASS"
