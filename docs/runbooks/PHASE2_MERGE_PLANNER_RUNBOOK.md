# Phase 2 Merge Planner Runbook

## Purpose
Build the first canon-facing merge plan from the quarantined archive inventory.

## Inputs
- `C:\NexusQuarantine\manifests\archive_inventory_summary.json`
- `C:\NexusQuarantine\fingerprints\archive_fingerprints.csv`
- `C:\NexusV3\registry\planning\PHASE2_ROLE_WEIGHTS.json`

## Outputs
- `phase2_merge_matrix.json`
- `phase2_repo_scorecard.csv`
- `phase2_selection_plan.json`
- `phase2_extraction_batches.json`
- `PHASE2_MERGE_PLAN.md`

## Canon rules
- Never merge whole repos.
- Prefer one winner per canon role, with alternates recorded.
- Treat tiny archives and capture packs as reference-only unless proven otherwise.
- Prefer richer product/UI candidates for shell and block layers.
- Prefer Nexus2.9 for integrated control-plane skeleton.
- Prefer SkylerOS-Truth for truth/gap methodology.

## Execution
Run:
`C:\NexusV3\Run-Nexus-Phase2-MergePlanner.ps1`
