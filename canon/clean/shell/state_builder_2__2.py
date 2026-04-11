import json
from pathlib import Path

from app.core.state_paths import (
    ARTIFACTS_PATH,
    CHECKPOINTS_PATH,
    JOBS_PATH,
    MESSAGES_PATH,
    STATE_ROOT,
    SUMMARY_PATH,
    ensure_state_root,
)
from app.db import get_conn


def _load_json(path: Path, default):
    ensure_state_root()
    if path.exists():
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    return default


def _row_to_memory_item(r):
    if isinstance(r, dict):
        updated_at = r.get("updated_at")
        return {
            "id": r.get("id"),
            "project_id": r.get("project_id"),
            "scope": r.get("scope"),
            "title": r.get("title"),
            "content": r.get("content"),
            "status": r.get("status"),
            "confidence": r.get("confidence"),
            "meta": r.get("meta"),
            "updated_at": str(updated_at) if updated_at is not None else None,
        }

    if hasattr(r, "keys"):
        keys = set(r.keys())
        updated_at = r["updated_at"] if "updated_at" in keys else None
        return {
            "id": r["id"] if "id" in keys else None,
            "project_id": r["project_id"] if "project_id" in keys else None,
            "scope": r["scope"] if "scope" in keys else None,
            "title": r["title"] if "title" in keys else None,
            "content": r["content"] if "content" in keys else None,
            "status": r["status"] if "status" in keys else None,
            "confidence": r["confidence"] if "confidence" in keys else None,
            "meta": r["meta"] if "meta" in keys else None,
            "updated_at": str(updated_at) if updated_at is not None else None,
        }

    updated_at = r[8] if len(r) > 8 else None
    return {
        "id": r[0] if len(r) > 0 else None,
        "project_id": r[1] if len(r) > 1 else None,
        "scope": r[2] if len(r) > 2 else None,
        "title": r[3] if len(r) > 3 else None,
        "content": r[4] if len(r) > 4 else None,
        "status": r[5] if len(r) > 5 else None,
        "confidence": r[6] if len(r) > 6 else None,
        "meta": r[7] if len(r) > 7 else None,
        "updated_at": str(updated_at) if updated_at is not None else None,
    }


def _search_memory(project_id: str, query: str) -> list[dict]:
    clauses = ["status = 'active'", "(project_id = %s or project_id is null)"]
    params = [project_id]

    if query:
        clauses.append("(title ilike %s or content ilike %s)")
        params.append(f"%{query}%")
        params.append(f"%{query}%")

    params.append(5)

    sql = f"""
        select id, project_id, scope, title, content, status, confidence, meta, updated_at
        from memory_records
        where {' and '.join(clauses)}
        order by updated_at desc, confidence desc
        limit %s
    """

    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, params)
        rows = cur.fetchall()

    return [_row_to_memory_item(r) for r in rows]


def _latest_checkpoint(project_id: str):
    checkpoints = _load_json(CHECKPOINTS_PATH, [])
    items = [c for c in checkpoints if c.get("project_id") == project_id]
    if not items:
        return None
    return items[-1]


def get_project_now(project_id: str, user_message: str = ""):
    messages = _load_json(MESSAGES_PATH, [])
    jobs = _load_json(JOBS_PATH, [])
    artifacts = _load_json(ARTIFACTS_PATH, [])
    summary = _load_json(SUMMARY_PATH, {})

    recent_messages = [m for m in messages if m.get("project_id") == project_id][-12:]
    recent_jobs = [j for j in jobs if j.get("project_id") == project_id][-12:]
    recent_artifacts = [a for a in artifacts if a.get("project_id") == project_id][-12:]
    latest_checkpoint = _latest_checkpoint(project_id)

    objective_title = summary.get("objective") or "Stabilize continuity and state layer"
    next_step_title = summary.get("next_step") or "Execution loop active: review latest artifact and continue operator cycle"
    search_query = (user_message or summary.get("last_input") or next_step_title or "").strip()
    relevant_memory = _search_memory(project_id, search_query)

    prioritized_actions = [
        {
            "id": "execute_next_step",
            "priority": "high",
            "kind": "next_step",
            "title": next_step_title,
            "reason": "This is the currently linked next step for the active objective.",
            "payload": {"project_id": project_id},
        },
        {
            "id": "capture_checkpoint",
            "priority": "medium",
            "kind": "checkpoint",
            "title": "Capture a fresh checkpoint",
            "reason": (
                "The project lacks a recent checkpoint, which weakens resume quality and compression readiness."
                if latest_checkpoint is None
                else "Capture a new checkpoint after meaningful progress."
            ),
            "payload": {"project_id": project_id},
        },
        {
            "id": "chain_workflow",
            "priority": "medium",
            "kind": "workflow",
            "title": "Chain the next workflow move",
            "reason": "Execution is succeeding and no blockers are open, so the system can move beyond single-step operation.",
            "payload": {
                "objective_id": None,
                "recent_completed_job_ids": [j.get("id") for j in recent_jobs[-3:]],
            },
        },
    ]

    if not relevant_memory:
        prioritized_actions.append(
            {
                "id": "strengthen_memory",
                "priority": "medium",
                "kind": "memory",
                "title": "Upsert a durable project memory",
                "reason": "No relevant durable memory surfaced for this context; adding one improves future continuity.",
                "payload": {"scope": "project"},
            }
        )

    prioritized_actions.append(
        {
            "id": "capture_ramble",
            "priority": "low",
            "kind": "ramble",
            "title": "Capture a freeform ramble input",
            "reason": "No ramble capture exists yet; freeform capture improves idea extraction and operator awareness.",
            "payload": {"project_id": project_id},
        }
    )

    return {
        "ok": True,
        "project_id": project_id,
        "project": {
            "id": project_id,
            "last_user_message": user_message,
            "state_root": str(STATE_ROOT),
        },
        "objective": {"title": objective_title},
        "next_step": {"title": next_step_title},
        "blockers": [],
        "recent_jobs": recent_jobs,
        "recent_artifacts": recent_artifacts,
        "recent_messages": recent_messages,
        "relevant_memory": relevant_memory,
        "latest_checkpoint": latest_checkpoint,
        "latest_ramble_capture": None,
        "operator": {
            "status": "stable",
            "summary": (
                f"Objective: {objective_title} | Next: {next_step_title} | "
                f"Memory: {len(relevant_memory)} signal(s)"
            ),
            "prioritized_actions": prioritized_actions,
            "workflow_chain": [
                next_step_title,
                "Capture a fresh checkpoint",
                "Chain the next workflow move",
            ],
            "signals": {
                "open_blockers": 0,
                "failed_jobs": 0,
                "queued_jobs": 0,
                "running_jobs": 0,
                "completed_jobs": len(recent_jobs),
                "recent_messages": len(recent_messages),
                "memory_signals": len(relevant_memory),
                "checkpoint_age_hours": None if latest_checkpoint is None else 0,
                "ramble_age_hours": None,
                "last_message_age_hours": None,
            },
            "richer_summary": {
                "objective_title": objective_title,
                "next_step_title": next_step_title,
                "top_blocker": None,
                "top_memory_titles": [m.get("title") for m in relevant_memory[:3]],
                "workflow_readiness": "ready" if recent_jobs else "forming",
            },
        },
        "next_suggested_actions": prioritized_actions,
        "continuity": {
            "recent_message_count": len(recent_messages),
            "memory_signal_count": len(relevant_memory),
            "recent_message_preview": [
                {
                    "id": m.get("id"),
                    "role": m.get("role"),
                    "content": m.get("content"),
                    "created_at": m.get("created_at"),
                }
                for m in recent_messages[-5:]
            ],
            "memory_signal_titles": [m.get("title") for m in relevant_memory[:5]],
            "latest_checkpoint_title": latest_checkpoint.get("title") if latest_checkpoint else None,
            "latest_ramble_capture_title": None,
        },
    }
