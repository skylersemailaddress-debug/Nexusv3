# Disaster Recovery Runbook

## Trigger conditions
- runtime validation fails and cannot be repaired quickly
- production data corruption suspected
- deployment causes service outage

## Immediate steps
1. Stop further changes
2. Restore latest frozen baseline
3. Run runtime validation
4. Verify health, action, dashboard, and UI
5. Export support bundle
6. Document incident and root cause

## Restore source
- `_baseline/` latest green snapshot
- `codex-rollback.ps1`

## Validation after restore
- `codex-validate.ps1`
