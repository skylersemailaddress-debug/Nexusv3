# Nexus V3 CI/CD and Release Discipline

## Current gate
- All changes must preserve `codex-validate.ps1`
- Green runtime validation is the minimum merge bar

## Required workflow
1. Checkout repo
2. Install backend dependencies
3. Install frontend dependencies
4. Start clean runtime
5. Run `codex-validate.ps1`
6. If green, create baseline snapshot
7. Promotion remains human-approved until later phases

## Promotion path
- dev
- staging
- production

## Rollback
Use:
- `codex-rollback.ps1` for local/runtime rollback
- latest frozen baseline snapshot as restore source

## Branch discipline
- protected main branch
- pull requests required
- status checks required
- no direct merges without green validation
