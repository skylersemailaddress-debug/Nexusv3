# TRUTH MAINTENANCE AND INVARIANT SPEC

## Purpose
Preserve canonical truth, detect drift, and enforce system invariants during autonomous execution.

## Required components
- invariant registry
- contradiction engine
- drift detector
- truth reconciliation engine
- rollback trigger logic

## Core invariants
- one runtime authority
- one auth authority
- one state authority
- one execution graph authority
- no whole-repo merge
- no promotion without proof

## Outputs
- invariant violations
- drift alerts
- rollback triggers
- reconciliation actions

## Tests required
- invariant violation detection
- drift report generation
- rollback trigger on conflicting promotion
