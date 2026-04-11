pwsh -NoProfile -ExecutionPolicy Bypass -File "C:\NexusV3\tools\canon\Compile-NexusCanon.ps1" -Root "C:\NexusV3"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
pwsh -NoProfile -ExecutionPolicy Bypass -File "C:\NexusV3\assembly\gates\Invoke-NexusGates.ps1" -Root "C:\NexusV3"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
