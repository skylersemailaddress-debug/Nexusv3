# Archive Expansion V2 Runbook

## Recommended flow
1. Put all source zip files in one folder, for example `C:\NexusArchiveDrop`.
2. Install the package into `C:\NexusV3`.
3. Run `Expand-And-Register-NexusArchiveSet.ps1` against that folder.
4. Review:
   - `C:\NexusQuarantine\manifests\archive_inventory_summary.json`
   - `C:\NexusQuarantine\fingerprints\archive_fingerprints.csv`
5. Use extraction records for canon imports.

## Example
```powershell
& "C:\NexusV3\tools\intake\Expand-And-Register-NexusArchiveSet.ps1" `
  -SourceRoot "C:\NexusArchiveDrop" `
  -NexusRoot "C:\NexusV3" `
  -QuarantineRoot "C:\NexusQuarantine" `
  -ExpandAll
```
