# RUNTIME AUTHORITY SPEC

## Purpose
Establish one durable, DB-backed runtime authority for state, migrations, queue, checkpoints, idempotency, and health.

## Authority
- durable runtime store: Postgres
- runtime truth owner: single runtime authority
- health is authoritative, not optimistic

## Required components
- migration runner
- queue engine
- checkpoint engine
- idempotency manager
- runtime verifier
- health authority
- request/trace id engine

## Inputs
- user intent
- execution requests
- queued jobs
- approval state
- persistence state

## Outputs
- state transitions
- queue outcomes
- checkpoints
- health states
- proofs

## Invariants
- no JSON as execution truth
- no SQLite in canonical runtime path
- one execution graph authority
- one auth authority
- one state backend

## Tests required
- migration pass/fail
- queue enqueue/dequeue
- checkpoint resume
- idempotent replay protection
- runtime health under degraded dependencies

## Done when
- all runtime mutations are audited
- all health probes read the same authority stack
- resume and rollback both work against live runtime state
