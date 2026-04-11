# Operations Runbook

## Daily technical checks
- runtime validation green
- latest CI gate green
- audit log writable
- request log writable
- support bundle export works

## Standard commands
- validate: `codex-validate.ps1`
- rollback: `codex-rollback.ps1`
- baseline snapshot: `runtime/ops/snapshot-baseline.ps1`
- support bundle: `runtime/ops/export-support-bundle.ps1`
