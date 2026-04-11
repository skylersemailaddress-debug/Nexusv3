param(
    [string]$Root = "C:\NexusV3"
)

$ErrorActionPreference = "Stop"

function Fail([string]$Message) {
    Write-Error $Message
    exit 1
}

Write-Host "[GATES] Running gate checks"

$requiredDirs = @(
    (Join-Path $Root "apps"),
    (Join-Path $Root "engines"),
    (Join-Path $Root "packs"),
    (Join-Path $Root "assembly\gates"),
    (Join-Path $Root "telemetry\auditor"),
    (Join-Path $Root "tools\factory"),
    (Join-Path $Root "tools\canon")
)

foreach ($dir in $requiredDirs) {
    if (-not (Test-Path -LiteralPath $dir)) {
        Fail "Missing required directory: $dir"
    }
}

$duplicateExecGraphs = Get-ChildItem -LiteralPath $Root -Recurse -File -Filter "*execution_graph*.json" -ErrorAction SilentlyContinue
if ($duplicateExecGraphs.Count -gt 1) {
    $paths = ($duplicateExecGraphs | Select-Object -ExpandProperty FullName) -join "; "
    Fail "Multiple execution graph artifacts detected: $paths"
}

Write-Host "[GATES] PASS"
