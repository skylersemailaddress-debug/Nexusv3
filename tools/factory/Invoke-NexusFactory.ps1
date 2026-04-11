param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("doctor", "compile", "gates", "audit", "all")]
    [string]$Command,
    [string]$Root = "C:\NexusV3"
)

$ErrorActionPreference = "Stop"

function Write-Factory([string]$Message) {
    Write-Host "[FACTORY] $Message"
}

switch ($Command) {
    "doctor" {
        Write-Factory "Running doctor checks"
        & (Join-Path $Root "tools\canon\Compile-NexusCanon.ps1") -Root $Root
        & (Join-Path $Root "assembly\gates\Invoke-NexusGates.ps1") -Root $Root
        & (Join-Path $Root "telemetry\auditor\Invoke-NexusAudit.ps1") -Root $Root
    }
    "compile" {
        & (Join-Path $Root "tools\canon\Compile-NexusCanon.ps1") -Root $Root
    }
    "gates" {
        & (Join-Path $Root "assembly\gates\Invoke-NexusGates.ps1") -Root $Root
    }
    "audit" {
        & (Join-Path $Root "telemetry\auditor\Invoke-NexusAudit.ps1") -Root $Root
    }
    "all" {
        Write-Factory "Running full factory pipeline"
        & (Join-Path $Root "tools\canon\Compile-NexusCanon.ps1") -Root $Root
        & (Join-Path $Root "assembly\gates\Invoke-NexusGates.ps1") -Root $Root
        & (Join-Path $Root "telemetry\auditor\Invoke-NexusAudit.ps1") -Root $Root
        Write-Factory "Full factory pipeline complete"
    }
}
