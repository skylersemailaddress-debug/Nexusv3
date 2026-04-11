# Phase 4 Execution Plan

## Objective
Stage semantically meaningful candidate files from locked primaries and allowed references into canon staging without whole-repo merges.

## Filters enforced
- excludes: .git, .venv, node_modules, site-packages, dist-info, generated, quarantine, archive
- excludes: LOCK, LOG, REQUESTED, .py.typed, .gitkeep, .journal, .wal, .db, .d.ts
- includes only target-relevant paths by layer semantics

## Outputs
- registry\phase4\phase4_execution_summary.json
- registry\phase4\phase4_promotion_manifest.json
- staging\phase4\*

## Rule
No staged file is canon authority until explicit promotion.
