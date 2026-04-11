# runtime/AGENTS.md

## Runtime authority
`runtime/` is the only executable surface.

## Allowed change zones
- `runtime/control/`
- `runtime/ui/`
- `runtime/ops/`
- `runtime/data/` only when explicitly required for workflow/data changes

## Backend rules
- Keep API routes working:
  - `/health`
  - `/action/test`
  - `/dashboard/status`
- If new routes are added, do not break existing validation.
- Prefer extracting routes/services rather than expanding monolithic files forever.

## Frontend rules
- Keep the app reachable on port 5173.
- Preserve existing validation path and visible operator surface.
- Avoid introducing framework churn.

## Mandatory validation
Run:
- `powershell -ExecutionPolicy Bypass -File .\codex-validate.ps1 -RepoRoot "<repo root>"`

## Rollback
If the runtime becomes unstable, run:
- `powershell -ExecutionPolicy Bypass -File .\codex-rollback.ps1 -RepoRoot "<repo root>"`
