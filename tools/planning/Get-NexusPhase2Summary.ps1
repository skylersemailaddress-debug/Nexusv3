param([string]$NexusRoot = 'C:\NexusV3')
$selectionPath = Join-Path $NexusRoot 'registry\planning\phase2_selection_plan.json'
if (-not (Test-Path $selectionPath)) { throw "Missing selection plan: $selectionPath" }
Get-Content -LiteralPath $selectionPath -Raw | ConvertFrom-Json
