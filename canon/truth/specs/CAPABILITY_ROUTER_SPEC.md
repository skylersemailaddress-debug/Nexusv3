# CAPABILITY ROUTER SPEC

## Purpose
Route work to the best execution path based on intent, profile, context, risk, and expected value.

## Required components
- capability registry
- input/output schemas
- precondition evaluator
- side-effect classifier
- cost model
- latency model
- confidence scorer
- fallback chain manager
- rollback strategy map

## Inputs
- user intent
- user profile
- workspace context
- risk level
- execution mode
- tool availability

## Outputs
- chosen capability
- ranked alternates
- execution contract
- rollback plan
- telemetry reason codes

## Invariants
- no high-risk action without explicit risk-aware routing
- no tool choice without declared schema and side effects
- fallback ordering must be deterministic

## Tests required
- route selection across user modes
- cost/latency tradeoff routing
- fallback on unavailable capability
- dangerous-action routing downgrade

## Done when
- all non-trivial actions flow through declared capability routing
- routing decisions are explainable via stored reason codes
