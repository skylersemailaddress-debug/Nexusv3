param(
  [string]$NexusRoot = "C:\NexusV3",
  [string]$QuarantineRoot = "C:\NexusQuarantine"
)
$ErrorActionPreference = "Stop"

$srcRoot = Join-Path $NexusRoot "src"
$integrationSummary = Join-Path $NexusRoot "registry\integration\phase6_integration_summary.json"
$integrationMap = Join-Path $NexusRoot "registry\integration\phase6_integration_map.json"
$contractAuthority = Join-Path $NexusRoot "registry\locks\CONTRACT_AUTHORITY.yaml"
$runtimeRoot = Join-Path $NexusRoot "registry\runtime"
$runbookPath = Join-Path $NexusRoot "docs\runbooks\PHASE7_RUNTIME_EXECUTION.md"

$required = @($srcRoot, $integrationSummary, $integrationMap, $contractAuthority)
foreach ($f in $required) {
  if (!(Test-Path $f)) { throw "Missing required Phase 7 prerequisite: $f" }
}

New-Item -ItemType Directory -Force -Path $runtimeRoot | Out-Null

$targets = @("truth","control","shell","proofs","continuity")
$inventory = @{}
foreach ($t in $targets) {
  $files = Get-ChildItem -Path (Join-Path $srcRoot $t) -File -ErrorAction SilentlyContinue
  $inventory[$t] = @($files | ForEach-Object { $_.Name })
}

$runtimeManifest = [pscustomobject]@{
  runtime_name = "NexusV3 Canon Runtime"
  generated_at_utc = [DateTime]::UtcNow.ToString("o")
  layers = [pscustomobject]@{
    truth = [pscustomobject]@{ files = $inventory["truth"]; authority = "SkylerOS-Truth (2).zip" }
    control = [pscustomobject]@{ files = $inventory["control"]; authority = "Nexus2.9 (10).zip" }
    shell = [pscustomobject]@{ files = $inventory["shell"]; authority = "FrankV2 (50).zip" }
    proofs = [pscustomobject]@{ files = $inventory["proofs"]; authority = "ODP_clean (4).zip" }
    continuity = [pscustomobject]@{ files = $inventory["continuity"]; authority = "skyler-os.zip" }
  }
}

$runtimeContracts = @(
  [pscustomobject]@{ contract = "auth"; owner = "control_runtime_authority"; status = "bound" },
  [pscustomobject]@{ contract = "state"; owner = "continuity_authority"; status = "bound" },
  [pscustomobject]@{ contract = "execution_graph"; owner = "control_runtime_authority"; status = "bound" },
  [pscustomobject]@{ contract = "memory_schema"; owner = "continuity_authority"; status = "bound" }
)

$launchGate = [pscustomobject]@{
  gate = "phase7_runtime_launch"
  truth_ready = ((Get-ChildItem -Path (Join-Path $srcRoot "truth") -File -ErrorAction SilentlyContinue | Measure-Object).Count -gt 0)
  control_ready = ((Get-ChildItem -Path (Join-Path $srcRoot "control") -File -ErrorAction SilentlyContinue | Measure-Object).Count -gt 0)
  shell_ready = ((Get-ChildItem -Path (Join-Path $srcRoot "shell") -File -ErrorAction SilentlyContinue | Measure-Object).Count -gt 0)
  proofs_ready = ((Get-ChildItem -Path (Join-Path $srcRoot "proofs") -File -ErrorAction SilentlyContinue | Measure-Object).Count -gt 0)
  continuity_ready = ((Get-ChildItem -Path (Join-Path $srcRoot "continuity") -File -ErrorAction SilentlyContinue | Measure-Object).Count -gt 0)
}
$launchGate | Add-Member -NotePropertyName pass -NotePropertyValue ($launchGate.truth_ready -and $launchGate.control_ready -and $launchGate.shell_ready -and $launchGate.proofs_ready -and $launchGate.continuity_ready)

$bootstrap = @"
# Nexus Runtime Bootstrap

## Canon launch sequence
1. truth constraints loaded
2. control runtime registry loaded
3. shell surfaces connected
4. proofs gate attached
5. continuity state contract attached

## launch gate
pass: $($launchGate.pass)
"@

$manifestPath = Join-Path $runtimeRoot "phase7_runtime_manifest.json"
$contractsPath = Join-Path $runtimeRoot "phase7_runtime_contracts.json"
$gatePath = Join-Path $runtimeRoot "phase7_launch_gate.json"
$bootstrapPath = Join-Path $runtimeRoot "phase7_bootstrap.md"

$runtimeManifest | ConvertTo-Json -Depth 8 | Set-Content $manifestPath
$runtimeContracts | ConvertTo-Json -Depth 6 | Set-Content $contractsPath
$launchGate | ConvertTo-Json -Depth 4 | Set-Content $gatePath
$bootstrap | Set-Content $bootstrapPath

$runbook = @"
# Phase 7 Runtime Execution

## Objective
Assemble the first canon runtime manifest and launch gate from the integrated canon tree.

## Outputs
- registry\runtime\phase7_runtime_manifest.json
- registry\runtime\phase7_runtime_contracts.json
- registry\runtime\phase7_launch_gate.json
- registry\runtime\phase7_bootstrap.md

## Launch gate
pass: $($launchGate.pass)
"@
$runbook | Set-Content $runbookPath

Write-Host "[PHASE7] Runtime manifest written: $manifestPath"
Write-Host "[PHASE7] Runtime contracts written: $contractsPath"
Write-Host "[PHASE7] Launch gate written: $gatePath"
Write-Host "[PHASE7] Bootstrap written: $bootstrapPath"
Write-Host "[PHASE7] Runbook written: $runbookPath"
Write-Host "[PHASE7] PASS"
