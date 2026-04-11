# SPEC GAP ENGINE SPEC

## Purpose
Detect missing, ambiguous, contradictory, or under-specified requirements before build or execution.

## Required components
- missing requirement detector
- ambiguity detector
- contradiction detector
- unresolved dependency detector
- confidence scorer
- spec repair proposal generator

## Inputs
- canon truth
- subsystem specs
- execution plan
- implementation plans

## Outputs
- gap reports
- ambiguity reports
- contradiction reports
- bounded repair proposals

## Invariants
- no silent guessing on red-zone gaps
- every contradiction must be surfaced
- repair proposals must cite the affected spec surface

## Tests required
- missing field detection
- conflict detection across two specs
- under-specified workflow detection
- confidence downgrade on ambiguous inputs

## Done when
- the system can stop an autobuilder before it invents around missing canon
