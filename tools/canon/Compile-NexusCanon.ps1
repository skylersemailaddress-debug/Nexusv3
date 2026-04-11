param(
    [string]$Root = "C:\NexusV3"
)

$ErrorActionPreference = "Stop"

function Fail([string]$Message) {
    Write-Error $Message
    exit 1
}

Write-Host "[CANON] Compiling canon rules"

$requiredFiles = @(
    (Join-Path $Root "canon\invariants\INVARIANTS.md"),
    (Join-Path $Root "canon\contracts\RUNTIME_CONTRACT.yaml"),
    (Join-Path $Root "canon\contracts\AUTH_CONTRACT.yaml"),
    (Join-Path $Root "canon\contracts\EXECUTION_GRAPH_CONTRACT.yaml"),
    (Join-Path $Root "docs\ops\MERGE_POLICY.md"),
    (Join-Path $Root "docs\ops\HYGIENE_POLICY.md")
)

foreach ($file in $requiredFiles) {
    if (-not (Test-Path -LiteralPath $file)) {
        Fail "Missing canonical file: $file"
    }
}

$forbiddenDirs = @(".venv", "node_modules", "__pycache__")
foreach ($name in $forbiddenDirs) {
    $matches = Get-ChildItem -LiteralPath $Root -Directory -Recurse -Force -ErrorAction SilentlyContinue | Where-Object { $_.Name -eq $name }
    if ($matches) {
        $paths = ($matches | Select-Object -ExpandProperty FullName) -join "; "
        Fail "Forbidden directory detected: $paths"
    }
}

$scanExtensions = @(".ps1", ".py", ".ts", ".tsx", ".js", ".json", ".yaml", ".yml", ".env", ".md")
$excludeNames = @(
    "Compile-NexusCanon.ps1",
    "apply_nexusv3_factory.ps1",
    "validate_nexusv3_factory.ps1"
)
$excludeRelativePrefixes = @(
    "tools\canon\",
    ".git\hooks\"
)

$rootPrefix = $Root.TrimEnd('\\') + '\\'
$scanFiles = Get-ChildItem -LiteralPath $Root -Recurse -File -ErrorAction SilentlyContinue | Where-Object {
    if ($_.Extension -notin $scanExtensions) { return $false }
    if ($_.Name -in $excludeNames) { return $false }
    $full = $_.FullName
    $relative = if ($full.StartsWith($rootPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        $full.Substring($rootPrefix.Length)
    } else {
        $full
    }
    foreach ($prefix in $excludeRelativePrefixes) {
        if ($relative.StartsWith($prefix, [System.StringComparison]::OrdinalIgnoreCase)) { return $false }
    }
    return $true
}

$tokenRegex = '(?i)(Bearer\s+dev-api-token|dev-api-token|\bsk-[A-Za-z0-9_-]{8,})'
$authTokenHits = $scanFiles | Select-String -Pattern $tokenRegex -ErrorAction SilentlyContinue

if ($authTokenHits) {
    $paths = ($authTokenHits | Select-Object -ExpandProperty Path -Unique) -join "; "
    Fail "Hardcoded token pattern detected: $paths"
}

Write-Host "[CANON] PASS"
