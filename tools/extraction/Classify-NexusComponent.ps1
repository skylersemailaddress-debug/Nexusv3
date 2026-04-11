param(
  [Parameter(Mandatory=$true)][string]$ScanResultJson
)

$ErrorActionPreference = "Stop"
$scan = $ScanResultJson | ConvertFrom-Json

$high = [int]$scan.summary.high
$medium = [int]$scan.summary.medium

$class = "ADAPT"
$rationale = "Defaulting to adapt under canon."

if ($high -ge 1) {
  $class = "CONCEPT_ONLY"
  $rationale = "High severity findings require rewrite or concept-only intake."
} elseif ($medium -eq 0 -and $high -eq 0) {
  $class = "ADOPT"
  $rationale = "No medium/high risks detected."
} elseif ($medium -ge 3) {
  $class = "ADAPT"
  $rationale = "Multiple medium findings require normalization."
}

if (@($scan.findings | Where-Object { $_.type -eq 'pollution' }).Count -ge 3) {
  $class = "REJECT"
  $rationale = "Excessive pollution detected."
}

[PSCustomObject]@{
  source = $scan.source
  classification = $class
  rationale = $rationale
} | ConvertTo-Json -Depth 4
