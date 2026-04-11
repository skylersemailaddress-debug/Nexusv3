param(
    [string]$Root = "C:\NexusV3"
)

$ErrorActionPreference = "Stop"

function Fail([string]$Message) {
    Write-Error $Message
    exit 1
}

Write-Host "[AUDITOR] Running drift audit"

$requiredTop = @("docs", "canon", "apps", "engines", "packs", "assembly", "telemetry", "tools", "generated", "tests")
foreach ($name in $requiredTop) {
    $path = Join-Path $Root $name
    if (-not (Test-Path -LiteralPath $path)) {
        Fail "Missing top-level path: $path"
    }
}

$quarantineLeak = Get-ChildItem -LiteralPath $Root -Recurse -Directory -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -match "quarantine|archive|legacy-lineages|duplicate-snapshots" }

if ($quarantineLeak) {
    $paths = ($quarantineLeak | Select-Object -ExpandProperty FullName) -join "; "
    Fail "Quarantine-style paths detected inside canonical repo: $paths"
}

Write-Host "[AUDITOR] PASS"
