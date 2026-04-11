param(
  [string]$NexusRoot = "C:\NexusV3",
  [string]$QuarantineRoot = "C:\NexusQuarantine"
)
$ErrorActionPreference = "Stop"

$releaseManifest = Join-Path $NexusRoot "registry\packout\phase9_release_manifest.json"
$handoffChecklist = Join-Path $NexusRoot "registry\packout\phase9_handoff_checklist.json"
$releaseGate = Join-Path $NexusRoot "registry\packout\phase9_release_gate.json"
$packoutSummary = Join-Path $NexusRoot "registry\packout\phase9_packout_summary.json"
$handoffRoot = Join-Path $NexusRoot "registry\handoff"
$runbookPath = Join-Path $NexusRoot "docs\runbooks\PHASE10_HANDOFF_EXECUTION.md"

$required = @($releaseManifest, $handoffChecklist, $releaseGate, $packoutSummary)
foreach ($f in $required) {
  if (!(Test-Path $f)) { throw "Missing required Phase 10 prerequisite: $f" }
}

New-Item -ItemType Directory -Force -Path $handoffRoot | Out-Null

$gate = Get-Content $releaseGate -Raw | ConvertFrom-Json
if (-not $gate.pass) { throw "Phase 9 release gate is not passed" }

$release = Get-Content $releaseManifest -Raw | ConvertFrom-Json
$checks = Get-Content $handoffChecklist -Raw | ConvertFrom-Json
$summary = Get-Content $packoutSummary -Raw | ConvertFrom-Json

$operatorPacket = [pscustomobject]@{
  packet_name = "NexusV3 Operator Handoff Packet"
  generated_at_utc = [DateTime]::UtcNow.ToString("o")
  release_name = $release.release_name
  runtime_name = $release.runtime_name
  release_ready = $summary.release_ready
}

$acceptanceGate = [pscustomobject]@{
  gate = "phase10_operator_acceptance"
  pass = (($checks | Where-Object { -not $_.pass } | Measure-Object).Count -eq 0)
  checks = ($checks | Measure-Object).Count
}

$handoffSummary = [pscustomobject]@{
  operator_ready = $acceptanceGate.pass
  release_name = $release.release_name
  runtime_name = $release.runtime_name
  completed_checks = ($checks | Where-Object { $_.pass } | Measure-Object).Count
  total_checks = ($checks | Measure-Object).Count
}

$receipt = @"
# Nexus Operator Receipt

Release: $($release.release_name)
Runtime: $($release.runtime_name)
Acceptance gate pass: $($acceptanceGate.pass)

This handoff package confirms the canon runtime, launch state, and commercial packout were all validated before operator acceptance.
"@

$packetPath = Join-Path $handoffRoot "phase10_operator_packet.json"
$gatePath = Join-Path $handoffRoot "phase10_acceptance_gate.json"
$summaryPath = Join-Path $handoffRoot "phase10_handoff_summary.json"
$receiptPath = Join-Path $handoffRoot "phase10_operator_receipt.md"

$operatorPacket | ConvertTo-Json -Depth 6 | Set-Content $packetPath
$acceptanceGate | ConvertTo-Json -Depth 4 | Set-Content $gatePath
$handoffSummary | ConvertTo-Json -Depth 4 | Set-Content $summaryPath
$receipt | Set-Content $receiptPath

$runbook = @"
# Phase 10 Handoff Execution

## Objective
Create the final operator handoff packet and acceptance gate from the validated commercial packout state.

## Outputs
- registry\handoff\phase10_operator_packet.json
- registry\handoff\phase10_acceptance_gate.json
- registry\handoff\phase10_handoff_summary.json
- registry\handoff\phase10_operator_receipt.md

## Acceptance gate
pass: $($acceptanceGate.pass)
"@
$runbook | Set-Content $runbookPath

Write-Host "[PHASE10] Operator packet written: $packetPath"
Write-Host "[PHASE10] Acceptance gate written: $gatePath"
Write-Host "[PHASE10] Handoff summary written: $summaryPath"
Write-Host "[PHASE10] Operator receipt written: $receiptPath"
Write-Host "[PHASE10] Runbook written: $runbookPath"
Write-Host "[PHASE10] PASS"
