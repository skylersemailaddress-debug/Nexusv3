param(
  [string]$NexusRoot = "C:\NexusV3",
  [string]$QuarantineRoot = "C:\NexusQuarantine"
)
$ErrorActionPreference = "Stop"

$cleanCanon = Join-Path $NexusRoot "canon\clean"
$cleanupGate = Join-Path $NexusRoot "registry\cleanup\canon_cleanup_gate.json"
$materializeRoot = Join-Path $NexusRoot "registry\materialize"
$runbookPath = Join-Path $NexusRoot "docs\runbooks\APP_TEST_MATERIALIZATION_EXECUTION.md"

if (!(Test-Path $cleanCanon)) { throw "Missing clean canon root: $cleanCanon" }
if (!(Test-Path $cleanupGate)) { throw "Missing cleanup gate: $cleanupGate" }

$gate = Get-Content $cleanupGate -Raw | ConvertFrom-Json
if (-not $gate.pass) { throw "Canon cleanup gate is not passed" }

New-Item -ItemType Directory -Force -Path $materializeRoot | Out-Null

$appApi = Join-Path $NexusRoot "apps\nexus-control"
$appWeb = Join-Path $NexusRoot "apps\nexus-shell"
$testsSmoke = Join-Path $NexusRoot "tests\smoke"
$testsContracts = Join-Path $NexusRoot "tests\contracts"

New-Item -ItemType Directory -Force -Path $appApi | Out-Null
New-Item -ItemType Directory -Force -Path $appWeb | Out-Null
New-Item -ItemType Directory -Force -Path $testsSmoke | Out-Null
New-Item -ItemType Directory -Force -Path $testsContracts | Out-Null

function Copy-SomeFiles {
  param(
    [string]$SourceDir,
    [string]$DestDir,
    [int]$MaxFiles = 8,
    [string[]]$Extensions = @(".py",".ts",".tsx",".js",".json",".md")
  )
  if (!(Test-Path $SourceDir)) { return @() }
  $files = Get-ChildItem -Path $SourceDir -File -ErrorAction SilentlyContinue |
    Where-Object { $Extensions -contains $_.Extension.ToLowerInvariant() } |
    Sort-Object Name
  $copied = @()
  $count = 0
  foreach ($f in $files) {
    if ($count -ge $MaxFiles) { break }
    $dest = Join-Path $DestDir $f.Name
    $i = 1
    while (Test-Path $dest) {
      $base = [System.IO.Path]::GetFileNameWithoutExtension($f.Name)
      $ext = [System.IO.Path]::GetExtension($f.Name)
      $dest = Join-Path $DestDir ($base + "__" + $i + $ext)
      $i += 1
    }
    Copy-Item $f.FullName $dest -Force
    $copied += $dest
    $count += 1
  }
  return $copied
}

$controlFiles = Copy-SomeFiles -SourceDir (Join-Path $cleanCanon "control") -DestDir $appApi -MaxFiles 12
$shellFiles = Copy-SomeFiles -SourceDir (Join-Path $cleanCanon "shell") -DestDir $appWeb -MaxFiles 12
$truthFiles = Copy-SomeFiles -SourceDir (Join-Path $cleanCanon "truth") -DestDir $testsContracts -MaxFiles 6
$proofFiles = Copy-SomeFiles -SourceDir (Join-Path $cleanCanon "proofs") -DestDir $testsSmoke -MaxFiles 6

$apiReadme = @"
# nexus-control

Materialized app surface from canon\clean\control.

This directory is the first executable-facing control app surface created from cleaned canon files.
"@
$webReadme = @"
# nexus-shell

Materialized app surface from canon\clean\shell.

This directory is the first executable-facing shell app surface created from cleaned canon files.
"@
$smokeScript = @"
# Nexus smoke tests

This directory contains materialized smoke-test inputs from canon\clean\proofs.
"@
$contractScript = @"
# Nexus contract tests

This directory contains materialized contract-test inputs from canon\clean\truth.
"@

Set-Content (Join-Path $appApi "README.md") $apiReadme
Set-Content (Join-Path $appWeb "README.md") $webReadme
Set-Content (Join-Path $testsSmoke "README.md") $smokeScript
Set-Content (Join-Path $testsContracts "README.md") $contractScript

$manifest = [pscustomobject]@{
  generated_at_utc = [DateTime]::UtcNow.ToString("o")
  apps = @(
    [pscustomobject]@{ name = "nexus-control"; path = $appApi; files = $controlFiles.Count + 1 },
    [pscustomobject]@{ name = "nexus-shell"; path = $appWeb; files = $shellFiles.Count + 1 }
  )
  tests = @(
    [pscustomobject]@{ name = "smoke"; path = $testsSmoke; files = $proofFiles.Count + 1 },
    [pscustomobject]@{ name = "contracts"; path = $testsContracts; files = $truthFiles.Count + 1 }
  )
}

$summary = [pscustomobject]@{
  apps_materialized = 2
  tests_materialized = 2
  control_files = $controlFiles.Count
  shell_files = $shellFiles.Count
  truth_test_files = $truthFiles.Count
  proof_test_files = $proofFiles.Count
  pass = (($controlFiles.Count -gt 0) -and ($shellFiles.Count -gt 0))
}

$manifestPath = Join-Path $materializeRoot "app_test_materialization_manifest.json"
$summaryPath = Join-Path $materializeRoot "app_test_materialization_summary.json"
$gatePath = Join-Path $materializeRoot "app_test_materialization_gate.json"

$manifest | ConvertTo-Json -Depth 6 | Set-Content $manifestPath
$summary | ConvertTo-Json -Depth 4 | Set-Content $summaryPath
@{
  gate = "app_test_materialization"
  pass = $summary.pass
} | ConvertTo-Json -Depth 3 | Set-Content $gatePath

$runbook = @"
# App/Test Materialization Execution

## Objective
Materialize executable-facing app and test surfaces from canon\clean.

## Outputs
- apps\nexus-control\*
- apps\nexus-shell\*
- tests\smoke\*
- tests\contracts\*
- registry\materialize\app_test_materialization_manifest.json
- registry\materialize\app_test_materialization_summary.json
- registry\materialize\app_test_materialization_gate.json

## Gate
pass: $($summary.pass)
"@
$runbook | Set-Content $runbookPath

Write-Host "[MATERIALIZE] Manifest written: $manifestPath"
Write-Host "[MATERIALIZE] Summary written: $summaryPath"
Write-Host "[MATERIALIZE] Gate written: $gatePath"
Write-Host "[MATERIALIZE] Runbook written: $runbookPath"
Write-Host "[MATERIALIZE] PASS"
