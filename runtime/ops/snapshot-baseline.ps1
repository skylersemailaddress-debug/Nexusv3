$repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$baselineRoot = Join-Path $repoRoot '_baseline'
if (-not (Test-Path $baselineRoot)) {
  New-Item -ItemType Directory -Path $baselineRoot -Force | Out-Null
}

$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$target = Join-Path $baselineRoot ("ci_green_" + $stamp)

New-Item -ItemType Directory -Path $target -Force | Out-Null
Copy-Item -Recurse -Force (Join-Path $repoRoot 'runtime') (Join-Path $target 'runtime')
if (Test-Path (Join-Path $repoRoot 'RUNTIME_LOCK.md')) {
  Copy-Item -Force (Join-Path $repoRoot 'RUNTIME_LOCK.md') (Join-Path $target 'RUNTIME_LOCK.md')
}

$manifest = @{
  created_at = (Get-Date).ToString('o')
  source = 'ci_green_snapshot'
  repo_root = $repoRoot
} | ConvertTo-Json -Depth 4

Set-Content -Path (Join-Path $target 'baseline_manifest.json') -Value $manifest -Encoding UTF8
Write-Host "Created CI baseline snapshot at $target"
