# 06. Memory, State, and Timeline

## Four memory classes

### 1. Raw event memory
Stores:
- original text or raw payload
- timestamp
- session
- source
- attachments

Purpose:
- forensic recall
- exact reconstruction
- timeline truth

### 2. Semantic memory
Stores:
- embedding-backed meaning
- concept-level retrieval
- fuzzy recall

Purpose:
- “remember that dog walking app idea”
- theme matching
- cross-session concept retrieval

### 3. Structured memory
Stores:
- extracted facts
- decisions
- entities
- preferences
- tags
- relationships

Purpose:
- routing
- dashboarding
- stateful reasoning
- reliable retrieval

### 4. Checkpoint memory
Stores:
- compressed session summaries
- milestone snapshots
- project phase summaries
- decision logs

Purpose:
- continuity without huge context windows
- long-term recall
- project evolution

## Memory write rules

Auto-write only if:
- decision made
- reusable idea captured
- durable preference inferred with sufficient confidence
- project state changed
- major artifact created
- important reference recorded

Do not auto-write:
- trivial acknowledgments
- redundant chatter
- low-signal filler
- every intermediate reasoning step

## State model

State is not memory.
State is current truth.

At minimum, each active project needs:
- objective
- next_step
- blockers
- active_mode
- pending_approvals
- active_jobs
- context_summary
- latest_checkpoint_id

## Timeline

Timeline is first-class.

Every important event should emit a timeline event:
- session start/end
- memory write
- project created
- idea thread created
- task created/completed
- artifact created
- checkpoint created
- routing decision
- important tool run

## Anti-blur model

Do not force all captured items into projects.

Use these object types:
- inbox items
- idea threads
- projects
- tasks
- artifacts
- memories
- checkpoints

A raw thought can live as an idea thread until enough confidence exists to promote or attach it.

## Timeline query examples

Supported query styles:
- exact time windows
- fuzzy time windows
- concept + time
- project + time
- idea-thread lineage
- session reconstruction
