param(
  [Parameter(Mandatory=$true)][string]$Root,
  [Parameter(Mandatory=$false)][string]$OnlyName = ""
)

$ErrorActionPreference = "Stop"

$registryPath = Join-Path $Root "registry\sources\SOURCE_REGISTRY.json"
$extractCmd = Join-Path $Root "Apply-NexusExtraction.ps1"

if (-not (Test-Path -LiteralPath $registryPath)) {
  throw "Source registry not found: $registryPath"
}
if (-not (Test-Path -LiteralPath $extractCmd)) {
  throw "Extraction command not found: $extractCmd"
}

$registry = Get-Content -LiteralPath $registryPath -Raw -Encoding UTF8 | ConvertFrom-Json
$sources = @($registry.sources | Where-Object { $_.enabled -eq $true })

if (-not [string]::IsNullOrWhiteSpace($OnlyName)) {
  $sources = @($sources | Where-Object { $_.name -eq $OnlyName })
}

if ($sources.Count -eq 0) {
  Write-Host "[SOURCE-BATCH] No enabled sources to process"
  exit 0
}

foreach ($src in $sources) {
  Write-Host "[SOURCE-BATCH] Processing $($src.name) -> $($src.subsystem)"
  & $extractCmd -Source $src.path -Subsystem $src.subsystem -Root $Root
  if (-not $?) {
    throw "Source batch failed for $($src.name)"
  }
}

Write-Host "[SOURCE-BATCH] PASS"
