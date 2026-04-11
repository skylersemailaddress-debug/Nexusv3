[CmdletBinding()]
param(
  [string[]]$SearchRoots,
  [string]$NexusRoot = 'C:\NexusV3',
  [switch]$VerboseProgress
)

$knownPath = Join-Path $NexusRoot 'registry\sources\KNOWN_ARCHIVES_V2.json'
$known = @()
if (Test-Path $knownPath) {
  $json = Get-Content $knownPath -Raw | ConvertFrom-Json
  $known = @($json.archives)
}
$knownMap = @{}
foreach ($k in $known) { $knownMap[$k.file.ToLowerInvariant()] = $k }

if (-not $SearchRoots -or $SearchRoots.Count -eq 0) {
  $SearchRoots = @(
    'C:\',
    'C:\Users',
    $env:USERPROFILE,
    (Join-Path $env:USERPROFILE 'Downloads'),
    (Join-Path $env:USERPROFILE 'Desktop'),
    (Join-Path $env:USERPROFILE 'Documents')
  ) | Where-Object { $_ -and (Test-Path $_) } | Select-Object -Unique
}

$results = New-Object System.Collections.Generic.List[object]
$seen = @{}
$preferredDirs = @('Downloads','Desktop','Documents','C:\')

foreach ($root in $SearchRoots) {
  if (-not (Test-Path $root)) { continue }
  if ($VerboseProgress) { Write-Host "[AUTO-ARCHIVE-DISCOVERY] Scanning root: $root" }

  try {
    Get-ChildItem -LiteralPath $root -File -Filter '*.zip' -Recurse -ErrorAction SilentlyContinue |
      ForEach-Object {
        $full = $_.FullName
        if ($seen.ContainsKey($full.ToLowerInvariant())) { return }
        $seen[$full.ToLowerInvariant()] = $true
        $name = $_.Name
        $lower = $name.ToLowerInvariant()
        $match = $knownMap[$lower]
        $isKnown = $null -ne $match
        $rank = if ($_.DirectoryName -match '\\Downloads($|\\)' -or $_.DirectoryName -match '\\Desktop($|\\)' -or $_.DirectoryName -match '\\Documents($|\\)') { 0 } elseif ($_.DirectoryName -eq 'C:\') { 1 } else { 2 }
        $results.Add([pscustomobject]@{
          file = $name
          full_path = $full
          directory = $_.DirectoryName
          size_bytes = $_.Length
          last_write_time_utc = $_.LastWriteTimeUtc.ToString('o')
          is_known = $isKnown
          family = if ($isKnown) { $match.family } else { '' }
          canon_role = if ($isKnown) { $match.canon_role } else { '' }
          search_rank = $rank
        }) | Out-Null
      }
  } catch {
    if ($VerboseProgress) { Write-Host "[AUTO-ARCHIVE-DISCOVERY] Warning: failed root $root : $($_.Exception.Message)" }
  }
}

$sorted = $results | Sort-Object -Property @(
  @{ Expression = 'is_known'; Descending = $true },
  @{ Expression = 'search_rank'; Descending = $false },
  @{ Expression = 'file'; Descending = $false },
  @{ Expression = 'full_path'; Descending = $false }
)
$sorted
