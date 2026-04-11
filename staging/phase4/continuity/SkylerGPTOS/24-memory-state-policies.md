# 24. Memory and State Policies

## Memory write policy
Auto-write candidates include:
- durable preferences
- project facts
- named entities and relationships
- decisions
- accepted plans
- checkpoints and milestones
- reusable references
- repeated workflow patterns above threshold

Do not auto-write:
- filler acknowledgments
- transient logs
- duplicated reformulations
- noise without future retrieval value

## Memory deduplication policy
Before writing a durable memory:
- compare semantic similarity
- compare structured keys/entity references
- prefer merge/update when the same fact is being refined
- preserve original source links even when consolidating

## Retrieval policy
Context builder blends, in order:
1. current state snapshot
2. recent session context
3. latest checkpoint/summary
4. highly relevant structured memories
5. highly relevant semantic memories
6. explicitly attached artifacts

## Token discipline
- bounded retrieval per layer
- summaries precede raw history
- semantically similar duplicates are collapsed
- irrelevant artifact content is never injected by default

## State policy
State represents current truth, not history.
Required current-truth fields include:
- active objective
- next step
- current mode
- blockers
- approvals
- active jobs
- latest significant artifact
- project health/status

## State resolution policy
When signals conflict, resolve in this order unless explicitly overridden:
1. explicit approved state change
2. latest successful workflow/tool write
3. latest user correction
4. derived inference from high-confidence context

## Compression policy
- session summaries trigger on length/time thresholds
- milestone checkpoints trigger on major state transitions
- compression never destroys raw event provenance
