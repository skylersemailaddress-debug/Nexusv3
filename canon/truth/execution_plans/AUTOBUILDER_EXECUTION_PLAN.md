# AUTOBUILDER EXECUTION PLAN

## Decision
Use a three-track execution program with one cross-cutting layer and one final hardening layer.

## Track 1 — Runtime + Control Plane
Build first:
- DB-backed runtime authority
- execution graph engine
- auth + permissions
- queue + checkpoint + resume
- health authority
- approvals, rollback, audit, trace ids

## Track 2 — Operator + Capability System
Build second, partially overlapping with Track 1:
- capability registry
- routing engine
- API-first execution
- browser execution
- verification loop
- recovery loop
- trust classes
- workflow packs

## Track 3 — UI + Product + Launch Engine
Build third, partially overlapping with Track 2:
- product intent to UI translator
- layout/interaction/flow engines
- full-stack generator
- deployment outputs
- behavioral smoke tests

## Cross-cutting layer — Memory + Personalization
Build in parallel:
- session/episodic/profile/policy memory
- user model compiler
- contradiction detector
- confidence/decay scoring
- selective writeback

## Final layer — Telemetry + Evolution + Enterprise Hardening
Build after the core system is working:
- outcome tracking
- failure analytics
- experiment framework
- promotion gates
- audit, secrets, env separation, observability, reliability

## Order rule
Do not build all remaining domains sequentially.
Do not overbuild memory before runtime.
Do not overbuild UI before execution works.
