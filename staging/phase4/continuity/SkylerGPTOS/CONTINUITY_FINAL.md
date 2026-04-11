# Skyler OS – Hardened Continuity Architecture (FINAL)

## CORE PRINCIPLE
Continuity is enforced at the API layer, not the model.

The model is stateless.
The backend is the brain.

## NON-NEGOTIABLE FLOW (EVERY TURN)

1. /context/bootstrap (REQUIRED)
2. model generates response
3. /context/finalize (REQUIRED)

If either step is skipped → system is invalid.

---

## BOOTSTRAP (READ PHASE)

POST /context/bootstrap

Loads:
- project state (projectResume)
- working context (buildContext)
- memory (memorySearch)
- recent messages
- recent jobs/artifacts

Returns:
- context_id
- context_version
- full state bundle

RULE:
No answer is valid without bootstrap.

---

## FINALIZE (WRITE PHASE)

POST /context/finalize

Writes:
- user message
- assistant response
- project state changes
- durable memory
- audit log

RULE:
Every turn must be persisted.

---

## CONTEXT LOCKING

Every stateful operation requires:
- context_id
- context_version

If stale → reject (409)

This prevents drift.

---

## TURN-LEVEL MEMORY (REQUIRED)

Store exact:
- last user message
- last assistant message

NOT summaries only.

This guarantees:
“resume to last sentence”

---

## MEMORY LAYERS

- project_state (source of truth)
- durable_memory (facts)
- working_memory (active)
- messages (full log)
- audit_events (everything)

Knowledge files are NOT memory.

---

## REPO ENFORCEMENT

Before ANY code change:
- MUST call repo/read or repo/search
- MUST use real file paths

If not → invalid response

---

## EXECUTION ENFORCEMENT

- No blind execution
- All execution via controlled endpoints
- All execution logged

---

## FAILURE CONDITIONS

System is invalid if:
- bootstrap not called
- finalize not called
- memory not checked when required
- repo not inspected before code changes
- stale context used

---

## RESULT

Skyler OS becomes:
- deterministic
- auditable
- drift-resistant
- fully persistent across chats

