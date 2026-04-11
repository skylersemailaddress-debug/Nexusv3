param(
  [Parameter(Mandatory=$true)]
  [string]$RepoRoot
)

$validateAll = Join-Path $RepoRoot 'runtime\ops\validate-all.ps1'
if (-not (Test-Path $validateAll)) { throw "Missing validator: $validateAll" }

Write-Host "Running Codex validation gate..."
& $validateAll
