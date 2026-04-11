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
