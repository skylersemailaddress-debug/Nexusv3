# NexusV3 Invariants

## Runtime
- Postgres is the single durable runtime state authority.
- JSON files are debug, proof, or export artifacts only.
- SQLite is forbidden in canonical runtime execution paths.
- There is one execution graph authority.

## Auth
- There is one active auth contract.
- Hardcoded tokens are forbidden.

## Merge
- No whole-repo merges.
- All imports are subsystem extractions with provenance.

## Product
- No UI may ship without loading, empty, error, and permission states.
- No release without proof and rollback.

## Evolution
- No self-improving change may promote without shadow proof or equivalent validation.
