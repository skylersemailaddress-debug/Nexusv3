param(
  [Parameter(Mandatory=$true)][string]$Root,
  [Parameter(Mandatory=$true)][string]$Name,
  [Parameter(Mandatory=$true)][string]$Path,
  [Parameter(Mandatory=$true)][string]$Subsystem,
  [Parameter(Mandatory=$false)][string]$Notes = "",
  [switch]$Disabled
)

$ErrorActionPreference = "Stop"

$registryPath = Join-Path $Root "registry\sources\SOURCE_REGISTRY.json"
if (-not (Test-Path -LiteralPath $registryPath)) {
  throw "Source registry not found: $registryPath"
}
if (-not (Test-Path -LiteralPath $Path)) {
  throw "Source path not found: $Path"
}

$registry = Get-Content -LiteralPath $registryPath -Raw -Encoding UTF8 | ConvertFrom-Json
if ($null -eq $registry.sources) {
  $registry | Add-Member -NotePropertyName sources -NotePropertyValue @()
}

$existing = @($registry.sources | Where-Object { $_.name -eq $Name })
if ($existing.Count -gt 0) {
  $registry.sources = @($registry.sources | Where-Object { $_.name -ne $Name })
}

$entry = [PSCustomObject]@{
  name = $Name
  path = (Resolve-Path -LiteralPath $Path).Path
  subsystem = $Subsystem
  enabled = (-not $Disabled.IsPresent)
  notes = $Notes
}

$registry.sources = @($registry.sources) + @($entry)
$registry | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $registryPath -Encoding UTF8
Write-Host "[SOURCE-REGISTRY] Registered source: $Name"
