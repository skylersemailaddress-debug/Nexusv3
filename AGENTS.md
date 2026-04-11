# AGENTS.md

## Purpose
This repository is currently in a controlled runtime-consolidation phase. The only executable authority surface is `runtime/`.

## Scope rules
- Prefer changes only inside `runtime/`.
- Do not modify `_baseline/`, `_archive/`, staging, evidence, or generated pack extraction directories unless explicitly instructed.
- Do not rename or remove `runtime/ops/start-clean.ps1`, `runtime/ops/start-all.ps1`, `runtime/ops/validate.ps1`, or `runtime/ops/validate-all.ps1`.
- Preserve ports:
  - API: 8000
  - UI: 5173

## Required commands
Before claiming success on any code change, run:
- `powershell -ExecutionPolicy Bypass -File .\codex-validate.ps1 -RepoRoot "<repo root>"`

If rollback is needed, run:
- `powershell -ExecutionPolicy Bypass -File .\codex-rollback.ps1 -RepoRoot "<repo root>"`

## Task strategy
- Prefer additive changes over destructive rewrites.
- Keep changes small and reversible.
- Preserve current runtime validation guarantees:
  1. API OK
  2. API action OK
  3. Dashboard status OK
  4. UI OK
  5. Nexus runtime validation PASSED

## Current priority order
1. Codex-safe repo contract
2. Durable storage + migrations
3. Backend modularization
4. Frontend modularization
5. Auth/RBAC
6. CI/CD
7. Enterprise safety and observability

## Definition of done for a change
A change is not done unless:
- files are updated successfully
- validation passes
- no runtime authority boundaries were violated
- rollback path still exists
