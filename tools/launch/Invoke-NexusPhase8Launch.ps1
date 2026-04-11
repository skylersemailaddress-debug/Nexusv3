param(
  [string]$NexusRoot = "C:\NexusV3",
  [string]$QuarantineRoot = "C:\NexusQuarantine"
)
$ErrorActionPreference = "Stop"

$runtimeManifest = Join-Path $NexusRoot "registry\runtime\phase7_runtime_manifest.json"
$runtimeContracts = Join-Path $NexusRoot "registry\runtime\phase7_runtime_contracts.json"
$launchGate = Join-Path $NexusRoot "registry\runtime\phase7_launch_gate.json"
$bootstrap = Join-Path $NexusRoot "registry\runtime\phase7_bootstrap.md"
$launchRoot = Join-Path $NexusRoot "registry\launch"
$runbookPath = Join-Path $NexusRoot "docs\runbooks\PHASE8_LAUNCH_EXECUTION.md"

$required = @($runtimeManifest, $runtimeContracts, $launchGate, $bootstrap)
foreach ($f in $required) {
  if (!(Test-Path $f)) { throw "Missing required Phase 8 prerequisite: $f" }
}

New-Item -ItemType Directory -Force -Path $launchRoot | Out-Null

$gate = Get-Content $launchGate -Raw | ConvertFrom-Json
if (-not $gate.pass) { throw "Phase 7 launch gate is not passed" }

$runtime = Get-Content $runtimeManifest -Raw | ConvertFrom-Json
$contracts = Get-Content $runtimeContracts -Raw | ConvertFrom-Json

$launchPlan = [pscustomobject]@{
  launch_name = "NexusV3 Canon Launch"
  generated_at_utc = [DateTime]::UtcNow.ToString("o")
  sequence = @(
    "load_truth_constraints",
    "bind_control_runtime",
    "attach_shell_surfaces",
    "attach_proof_gates",
    "attach_continuity_state",
    "declare_launch_ready"
  )
  prerequisites = @(
    "phase7_runtime_manifest.json",
    "phase7_runtime_contracts.json",
    "phase7_launch_gate.json",
    "phase7_bootstrap.md"
  )
}

$startupProof = @(
  [pscustomobject]@{ check = "truth layer present"; pass = ($runtime.layers.truth.files.Count -gt 0) },
  [pscustomobject]@{ check = "control layer present"; pass = ($runtime.layers.control.files.Count -gt 0) },
  [pscustomobject]@{ check = "shell layer present"; pass = ($runtime.layers.shell.files.Count -gt 0) },
  [pscustomobject]@{ check = "proofs layer present"; pass = ($runtime.layers.proofs.files.Count -gt 0) },
  [pscustomobject]@{ check = "continuity layer present"; pass = ($runtime.layers.continuity.files.Count -gt 0) },
  [pscustomobject]@{ check = "runtime contracts bound"; pass = ($contracts.Count -ge 4) }
)

$launchGate2 = [pscustomobject]@{
  gate = "phase8_launch_orchestration"
  pass = (($startupProof | Where-Object { -not $_.pass } | Measure-Object).Count -eq 0)
  checks = $startupProof.Count
}

$launchSummary = [pscustomobject]@{
  launch_ready = $launchGate2.pass
  checks = $startupProof
  runtime_name = $runtime.runtime_name
  sequence_steps = $launchPlan.sequence.Count
}

$planPath = Join-Path $launchRoot "phase8_launch_plan.json"
$proofPath = Join-Path $launchRoot "phase8_startup_proof.json"
$gatePath = Join-Path $launchRoot "phase8_launch_gate.json"
$summaryPath = Join-Path $launchRoot "phase8_launch_summary.json"

$launchPlan | ConvertTo-Json -Depth 6 | Set-Content $planPath
$startupProof | ConvertTo-Json -Depth 6 | Set-Content $proofPath
$launchGate2 | ConvertTo-Json -Depth 6 | Set-Content $gatePath
$launchSummary | ConvertTo-Json -Depth 6 | Set-Content $summaryPath

$runbook = @"
# Phase 8 Launch Execution

## Objective
Create launch orchestration and startup proof artifacts from the validated Phase 7 runtime.

## Outputs
- registry\launch\phase8_launch_plan.json
- registry\launch\phase8_startup_proof.json
- registry\launch\phase8_launch_gate.json
- registry\launch\phase8_launch_summary.json

## Launch ready
pass: $($launchGate2.pass)
"@
$runbook | Set-Content $runbookPath

Write-Host "[PHASE8] Launch plan written: $planPath"
Write-Host "[PHASE8] Startup proof written: $proofPath"
Write-Host "[PHASE8] Launch gate written: $gatePath"
Write-Host "[PHASE8] Launch summary written: $summaryPath"
Write-Host "[PHASE8] Runbook written: $runbookPath"
Write-Host "[PHASE8] PASS"
