param(
  [Parameter(Mandatory=$true)]
  [string]$RepoRoot
)

$baselineRoot = Join-Path $RepoRoot '_baseline'
if (-not (Test-Path $baselineRoot)) { throw "Missing baseline root: $baselineRoot" }

$latest = Get-ChildItem -Path $baselineRoot -Directory | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $latest) { throw "No baseline snapshots found under $baselineRoot" }

$runtimeSrc = Join-Path $latest.FullName 'runtime'
$lockSrc = Join-Path $latest.FullName 'RUNTIME_LOCK.md'
$runtimeDst = Join-Path $RepoRoot 'runtime'
$lockDst = Join-Path $RepoRoot 'RUNTIME_LOCK.md'

if (-not (Test-Path $runtimeSrc)) { throw "Latest baseline does not contain runtime: $runtimeSrc" }

Write-Host "Restoring runtime from baseline: $($latest.FullName)"
if (Test-Path $runtimeDst) {
  Remove-Item -Recurse -Force $runtimeDst
}
Copy-Item -Recurse -Force $runtimeSrc $runtimeDst

if (Test-Path $lockSrc) {
  Copy-Item -Force $lockSrc $lockDst
}

Write-Host "Rollback restore complete."
Write-Host "Next: run runtime\ops\start-clean.ps1 then runtime\ops\validate-all.ps1"
