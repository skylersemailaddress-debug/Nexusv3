# AUTORUNNER POLICY GATE SPEC

## Purpose
Stop the autorunner from executing outside approved bounds.

## Required components
- policy loader
- side-effect policy evaluator
- approval gate
- environment gate
- promotion gate
- emergency stop

## Inputs
- action plan
- autonomy zone
- risk class
- environment target
- approval context

## Outputs
- allow
- deny
- escalate
- require approval
- stop execution

## Invariants
- production-impacting actions require explicit eligibility
- missing policy context defaults to deny or escalate
- emergency stop overrides all execution

## Tests required
- deny on missing approval
- deny on production target without clearance
- stop on invariant breach
