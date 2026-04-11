# AUTONOMY ZONE SPEC

## Purpose
Define bounded autonomy modes for the autorunner.

## Zones
- RED: spec-only, no inference, approval required for unresolved gaps
- YELLOW: constrained inference within declared subsystem and policy bounds
- GREEN: low-risk free generation within approved patterns

## Required components
- zone classifier
- risk classifier
- approval gate
- escalation engine
- zone transition rules

## Inputs
- task type
- risk level
- side-effect profile
- spec completeness
- policy context

## Outputs
- zone assignment
- execution constraints
- escalation requirements

## Invariants
- unresolved high-risk work cannot enter green zone
- red zone cannot bypass approval
- zone assignment must be explainable

## Tests required
- red/yellow/green assignment
- escalation on ambiguity
- approval enforcement on red work
