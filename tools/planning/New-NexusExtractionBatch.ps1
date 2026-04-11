param(
  [string]$NexusRoot = 'C:\NexusV3',
  [string]$Batch = 'B1_truth_and_governance'
)
$ErrorActionPreference = 'Stop'
$batchPath = Join-Path $NexusRoot 'registry\planning\phase2_extraction_batches.json'
$templatePath = Join-Path $NexusRoot 'templates\extraction\PHASE2_EXTRACTION_RECORD_TEMPLATE.md'
if (-not (Test-Path $batchPath)) { throw "Missing extraction batches: $batchPath" }
if (-not (Test-Path $templatePath)) { throw "Missing template: $templatePath" }
$batches = Get-Content -LiteralPath $batchPath -Raw | ConvertFrom-Json
$selected = $batches | Where-Object { $_.batch -eq $Batch } | Select-Object -First 1
if ($null -eq $selected) { throw "Unknown batch: $Batch" }
$outDir = Join-Path $NexusRoot ("docs\extraction\$Batch")
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
$template = Get-Content -LiteralPath $templatePath -Raw
foreach ($item in $selected.items) {
  $out = Join-Path $outDir ("$($item.primary_slug)_EXTRACTION.md")
  $body = $template -replace 'Extraction ID:', "Extraction ID: $($Batch)-$($item.primary_slug)"
  $body = $body -replace 'Source archive:', "Source archive: $($item.primary)"
  $body = $body -replace 'Canon target subsystem:', "Canon target subsystem: $($item.subsystem)"
  Set-Content -LiteralPath $out -Value $body -Encoding UTF8
  Write-Host "[PHASE2-EXTRACTION-BATCH] Wrote $out"
}
