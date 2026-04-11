# SIMULATION AND JUDGMENT SPEC

## Purpose
Evaluate multiple build options before committing.

## Required components
- option generator
- tradeoff evaluator
- future-cost simulator
- reversibility scorer
- operator-burden scorer
- value/risk ranking engine

## Inputs
- build intent
- subsystem specs
- policy/risk model
- deployment targets

## Outputs
- ranked options
- tradeoff report
- chosen plan with justification

## Invariants
- non-trivial builds should compare alternatives
- chosen option must record why it won
- irreversible/high-risk options require explicit approval

## Tests required
- option ranking
- reversibility downgrade
- cost/risk tradeoff comparison
