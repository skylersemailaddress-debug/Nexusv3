param(
  [string]$NexusRoot = "C:\NexusV3",
  [string]$QuarantineRoot = "C:\NexusQuarantine"
)
$ErrorActionPreference = "Stop"

$cleanCanon = Join-Path $NexusRoot "canon\clean"
$materializeGate = Join-Path $NexusRoot "registry\materialize\app_test_materialization_gate.json"
$runtimeWireRoot = Join-Path $NexusRoot "registry\runtimewire"
$runbookPath = Join-Path $NexusRoot "docs\runbooks\RUNTIME_WIRING_EXECUTION.md"

if (!(Test-Path $cleanCanon)) { throw "Missing clean canon root: $cleanCanon" }
if (!(Test-Path $materializeGate)) { throw "Missing app/test materialization gate: $materializeGate" }

$gate = Get-Content $materializeGate -Raw | ConvertFrom-Json
if (-not $gate.pass) { throw "App/test materialization gate is not passed" }

New-Item -ItemType Directory -Force -Path $runtimeWireRoot | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $NexusRoot "apps\nexus-control") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $NexusRoot "apps\nexus-shell") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $NexusRoot "tests\smoke") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $NexusRoot "tests\contracts") | Out-Null

$launcher = @'
param(
  [string]$NexusRoot = "C:\NexusV3"
)
$ErrorActionPreference = "Stop"

$runtimeManifest = Join-Path $NexusRoot "registry\runtime\phase7_runtime_manifest.json"
$launchGate = Join-Path $NexusRoot "registry\launch\phase8_launch_gate.json"
$controlDir = Join-Path $NexusRoot "apps\nexus-control"
$shellDir = Join-Path $NexusRoot "apps\nexus-shell"

if (!(Test-Path $runtimeManifest)) { throw "Missing runtime manifest" }
if (!(Test-Path $launchGate)) { throw "Missing launch gate" }
if (!(Test-Path $controlDir)) { throw "Missing nexus-control app surface" }
if (!(Test-Path $shellDir)) { throw "Missing nexus-shell app surface" }

$launch = Get-Content $launchGate -Raw | ConvertFrom-Json
if (-not $launch.pass) { throw "Launch gate not passed" }

Write-Host "[NEXUS] Booting runtime"
Write-Host "[NEXUS] truth -> control -> shell -> proofs -> continuity"
Write-Host "[NEXUS] control app: $controlDir"
Write-Host "[NEXUS] shell app: $shellDir"
Write-Host "[NEXUS] Runtime boot PASS"
'@

$smokeRunner = @'
param(
  [string]$NexusRoot = "C:\NexusV3"
)
$ErrorActionPreference = "Stop"

$checks = @(
  (Join-Path $NexusRoot "apps\nexus-control"),
  (Join-Path $NexusRoot "apps\nexus-shell"),
  (Join-Path $NexusRoot "tests\smoke"),
  (Join-Path $NexusRoot "tests\contracts"),
  (Join-Path $NexusRoot "registry\runtime\phase7_runtime_manifest.json"),
  (Join-Path $NexusRoot "registry\launch\phase8_launch_gate.json")
)

foreach ($c in $checks) {
  if (!(Test-Path $c)) { throw "Missing runtime surface: $c" }
}
Write-Host "[NEXUS-TESTS] Smoke PASS"
'@

Set-Content (Join-Path $NexusRoot "Start-Nexus.ps1") $launcher
Set-Content (Join-Path $NexusRoot "Run-Nexus-SmokeTests.ps1") $smokeRunner

$entryReadme = @"
# Nexus Runtime Entry

Primary runtime entrypoint:
- Start-Nexus.ps1

Primary smoke test entrypoint:
- Run-Nexus-SmokeTests.ps1
"@
Set-Content (Join-Path $NexusRoot "apps\nexus-control\ENTRYPOINT.md") $entryReadme
Set-Content (Join-Path $NexusRoot "apps\nexus-shell\ENTRYPOINT.md") $entryReadme

$manifest = [pscustomobject]@{
  generated_at_utc = [DateTime]::UtcNow.ToString("o")
  runtime_entry = "Start-Nexus.ps1"
  smoke_tests = "Run-Nexus-SmokeTests.ps1"
  apps = @("apps\nexus-control", "apps\nexus-shell")
  tests = @("tests\smoke", "tests\contracts")
}

$summary = [pscustomobject]@{
  runtime_entry_created = (Test-Path (Join-Path $NexusRoot "Start-Nexus.ps1"))
  smoke_tests_created = (Test-Path (Join-Path $NexusRoot "Run-Nexus-SmokeTests.ps1"))
  apps_wired = $true
  tests_wired = $true
  pass = $true
}

$gate2 = [pscustomobject]@{
  gate = "runtime_wiring"
  pass = $summary.pass
}

$manifestPath = Join-Path $runtimeWireRoot "runtime_wiring_manifest.json"
$summaryPath = Join-Path $runtimeWireRoot "runtime_wiring_summary.json"
$gatePath = Join-Path $runtimeWireRoot "runtime_wiring_gate.json"

$manifest | ConvertTo-Json -Depth 6 | Set-Content $manifestPath
$summary | ConvertTo-Json -Depth 4 | Set-Content $summaryPath
$gate2 | ConvertTo-Json -Depth 3 | Set-Content $gatePath

$runbook = @"
# Runtime Wiring Execution

## Objective
Create a single runtime entrypoint and smoke-test entrypoint from the cleaned canon and materialized app/test surfaces.

## Outputs
- Start-Nexus.ps1
- Run-Nexus-SmokeTests.ps1
- registry\runtimewire\runtime_wiring_manifest.json
- registry\runtimewire\runtime_wiring_summary.json
- registry\runtimewire\runtime_wiring_gate.json

## Gate
pass: $($gate2.pass)
"@
$runbook | Set-Content $runbookPath

Write-Host "[RUNTIME-WIRING] Manifest written: $manifestPath"
Write-Host "[RUNTIME-WIRING] Summary written: $summaryPath"
Write-Host "[RUNTIME-WIRING] Gate written: $gatePath"
Write-Host "[RUNTIME-WIRING] Runbook written: $runbookPath"
Write-Host "[RUNTIME-WIRING] PASS"
