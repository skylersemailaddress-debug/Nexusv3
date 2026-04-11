$repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$outDir = Join-Path $repoRoot 'runtime\support'
New-Item -ItemType Directory -Path $outDir -Force | Out-Null

$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$bundle = Join-Path $outDir ("support_bundle_" + $stamp)

New-Item -ItemType Directory -Path $bundle -Force | Out-Null

$paths = @(
  'runtime\logs',
  'runtime\data',
  'runtime\ops\validate.ps1',
  'runtime\ops\validate-all.ps1',
  'runtime\control\main.py'
)

foreach ($rel in $paths) {
  $src = Join-Path $repoRoot $rel
  if (Test-Path $src) {
    Copy-Item -Recurse -Force $src (Join-Path $bundle (Split-Path $rel -Leaf))
  }
}

Write-Host "Support bundle exported to $bundle"
