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
