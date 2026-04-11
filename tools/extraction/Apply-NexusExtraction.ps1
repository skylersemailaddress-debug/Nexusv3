param(
  [Parameter(Mandatory=$true)][string]$Root,
  [Parameter(Mandatory=$true)][string]$Source,
  [Parameter(Mandatory=$false)][string]$Subsystem = "unclassified"
)

$ErrorActionPreference = "Stop"

function Write-Info([string]$msg) {
  Write-Host "[EXTRACTION] $msg"
}

$scanScript = Join-Path $Root "tools\extraction\Scan-NexusSource.ps1"
$classifyScript = Join-Path $Root "tools\extraction\Classify-NexusComponent.ps1"
$normalizeScript = Join-Path $Root "tools\extraction\Normalize-NexusComponent.ps1"

$stagingRoot = Join-Path $Root "generated\staging"
$registryRoot = Join-Path $Root "registry\extractions"
New-Item -ItemType Directory -Force -Path $stagingRoot | Out-Null
New-Item -ItemType Directory -Force -Path $registryRoot | Out-Null

Write-Info "Scanning source"
$scanJson = & $scanScript -SourcePath $Source
$scan = $scanJson | ConvertFrom-Json

Write-Info "Classifying source"
$classJson = & $classifyScript -ScanResultJson $scanJson
$class = $classJson | ConvertFrom-Json

$id = "extract_" + (Get-Date -Format "yyyyMMdd_HHmmss")
$stagingPath = Join-Path $stagingRoot (Join-Path $Subsystem $id)

if ($class.classification -in @("ADOPT","ADAPT")) {
  Write-Info "Normalizing source into staging"
  & $normalizeScript -SourcePath $Source -DestinationPath $stagingPath
} else {
  Write-Info "Skipping normalization due to classification: $($class.classification)"
}

$record = [PSCustomObject]@{
  id = $id
  created_at = (Get-Date).ToString("s")
  source = $scan.source
  subsystem = $Subsystem
  classification = $class.classification
  rationale = $class.rationale
  findings = $scan.findings
  staging_path = $(if (Test-Path -LiteralPath $stagingPath) { $stagingPath } else { $null })
}

$recordPath = Join-Path $registryRoot ($id + ".json")
$record | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $recordPath -Encoding UTF8

Write-Info "Extraction record written"
Write-Host $recordPath
