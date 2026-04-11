param(
  [Parameter(Mandatory=$true)][string]$SourcePath,
  [Parameter(Mandatory=$true)][string]$DestinationPath
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $SourcePath)) {
  throw "Source path not found: $SourcePath"
}

New-Item -ItemType Directory -Force -Path $DestinationPath | Out-Null
$resolvedSource = (Resolve-Path -LiteralPath $SourcePath).Path

Get-ChildItem -LiteralPath $SourcePath -Recurse -Force | ForEach-Object {
  $full = $_.FullName
  if ($full -match '\\node_modules($|\\)' -or $full -match '\\\.venv($|\\)' -or $full -match '\\venv($|\\)') {
    return
  }

  $relative = $full.Substring($resolvedSource.Length).TrimStart('\')
  if ([string]::IsNullOrWhiteSpace($relative)) { return }
  $dest = Join-Path $DestinationPath $relative

  if ($_.PSIsContainer) {
    New-Item -ItemType Directory -Force -Path $dest | Out-Null
  } else {
    $parent = Split-Path -Parent $dest
    New-Item -ItemType Directory -Force -Path $parent | Out-Null
    Copy-Item -LiteralPath $full -Destination $dest -Force
  }
}
