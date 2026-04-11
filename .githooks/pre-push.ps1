pwsh -NoProfile -ExecutionPolicy Bypass -File "C:\NexusV3\tools\factory\Invoke-NexusFactory.ps1" -Command all -Root "C:\NexusV3"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
