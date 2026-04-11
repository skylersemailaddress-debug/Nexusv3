from __future__ import annotations

from typing import Any

from app.db import get_conn


RECENT_MESSAGE_LIMIT = 12
RECENT_JOB_LIMIT = 12
RECENT_ARTIFACT_LIMIT = 12
MEMORY_LIMIT = 5


def _coalesce_content(row: dict[str, Any]) -> str:
    return row.get("content_text") or row.get("content") or ""


def _normalize_message(row: dict[str, Any]) -> dict[str, Any]:
    meta = row.get("meta") or {}
    return {
        "id": meta.get("external_id") or f"msg_db_{row.get('id')}",
        "db_id": row.get("id"),
        "project_id": row.get("project_id"),
        "role": row.get("role"),
        "content": _coalesce_content(row),
        "meta": meta,
        "sequence_no": row.get("sequence_no"),
        "created_at": row.get("created_at"),
    }


def _normalize_memory(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row.get("id"),
        "project_id": row.get("project_id"),
        "scope": row.get("scope"),
        "title": row.get("title"),
        "content": row.get("content"),
        "status": row.get("status"),
        "confidence": row.get("confidence"),
        "meta": row.get("meta") or {},
        "updated_at": row.get("updated_at"),
    }


def _fetch_project_context(project_id: str, user_message: str) -> dict[str, Any]:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            insert into projects (id, name, status)
            values (%s, %s, 'active')
            on conflict (id) do nothing
            returning id
            """,
            (project_id, project_id),
        )
        conn.commit()

        cur.execute("select * from projects where id = %s", (project_id,))
        project = cur.fetchone() or {"id": project_id, "name": project_id, "status": "active", "meta": {}}

        cur.execute(
            """
            select id, project_id, role, content, content_text, content_structured, meta, sequence_no, created_at
            from messages
            where project_id = %s
            order by sequence_no desc, created_at desc, id desc
            limit %s
            """,
            (project_id, RECENT_MESSAGE_LIMIT),
        )
        recent_messages = [_normalize_message(r) for r in reversed(cur.fetchall())]

        cur.execute(
            """
            select *
            from jobs
            where project_id = %s
            order by created_at desc, id desc
            limit %s
            """,
            (project_id, RECENT_JOB_LIMIT),
        )
        recent_jobs = cur.fetchall()

        cur.execute(
            """
            select id, project_id, kind, title, path, payload, meta, created_at, updated_at
            from artifacts
            where project_id = %s
            order by created_at desc, id desc
            limit %s
            """,
            (project_id, RECENT_ARTIFACT_LIMIT),
        )
        recent_artifacts = cur.fetchall()

        cur.execute(
            """
            select *
            from project_state
            where project_id = %s
            limit 1
            """,
            (project_id,),
        )
        project_state = cur.fetchone()

        current_objective_id = project.get("current_objective_id")
        state_structured = (project_state or {}).get("structured_state") or {}
        structured_objective_id = state_structured.get("current_objective_id")
        structured_next_step_id = state_structured.get("next_step_id")
        blocker_ids_open = state_structured.get("blocker_ids_open") or []

        objective_id = current_objective_id or structured_objective_id
        objective = None
        if objective_id:
            cur.execute("select * from objectives where id = %s and project_id = %s", (objective_id, project_id))
            objective = cur.fetchone()

        if objective is None and project_state and project_state.get("current_objective"):
            cur.execute(
                """
                select *
                from objectives
                where project_id = %s and title = %s
                order by updated_at desc, created_at desc
                limit 1
                """,
                (project_id, project_state.get("current_objective")),
            )
            objective = cur.fetchone()

        next_step = None
        next_step_id = structured_next_step_id or (objective or {}).get("next_step_id")
        if next_step_id:
            cur.execute("select * from next_steps where id = %s and project_id = %s", (next_step_id, project_id))
            next_step = cur.fetchone()

        if next_step is None and project_state and project_state.get("next_step"):
            cur.execute(
                """
                select *
                from next_steps
                where project_id = %s and title = %s
                order by updated_at desc, created_at desc
                limit 1
                """,
                (project_id, project_state.get("next_step")),
            )
            next_step = cur.fetchone()

        if next_step is None and objective is not None:
            cur.execute(
                """
                select *
                from next_steps
                where project_id = %s and objective_id = %s
                order by updated_at desc, created_at desc
                limit 1
                """,
                (project_id, objective.get("id")),
            )
            next_step = cur.fetchone()

        blockers = []
        if blocker_ids_open:
            cur.execute(
                """
                select *
                from blockers
                where project_id = %s and id = any(%s) and status = 'open'
                order by updated_at desc, created_at desc
                """,
                (project_id, blocker_ids_open),
            )
            blockers = cur.fetchall()
        else:
            cur.execute(
                """
                select *
                from blockers
                where project_id = %s and status = 'open'
                order by updated_at desc, created_at desc
                limit 10
                """,
                (project_id,),
            )
            blockers = cur.fetchall()

        search_query = (user_message or "").strip()

        clauses = ["status = 'active'", "(project_id = %s or project_id is null)"]
        params: list[Any] = [project_id]
        if search_query:
            clauses.append("(title ilike %s or content ilike %s)")
            params.extend([f"%{search_query}%", f"%{search_query}%"])
        params.append(MEMORY_LIMIT)

        cur.execute(
            f"""
            select id, project_id, scope, title, content, status, confidence, meta, updated_at
            from memory_records
            where {' and '.join(clauses)}
            order by updated_at desc, confidence desc
            limit %s
            """,
            params,
        )
        relevant_memory = [_normalize_memory(r) for r in cur.fetchall()]

        cur.execute(
            """
            select id, project_id, kind, title, path, payload, meta, created_at, updated_at
            from artifacts
            where project_id = %s and kind = 'checkpoint'
            order by created_at desc, id desc
            limit 1
            """,
            (project_id,),
        )
        latest_checkpoint = cur.fetchone()

        cur.execute(
            """
            select id, project_id, kind, title, path, payload, meta, created_at, updated_at
            from artifacts
            where project_id = %s and kind = 'ramble_capture'
            order by created_at desc, id desc
            limit 1
            """,
            (project_id,),
        )
        latest_ramble_capture = cur.fetchone()

    return {
        "project": project,
        "project_state": project_state,
        "objective": objective,
        "next_step": next_step,
        "blockers": blockers,
        "recent_messages": recent_messages,
        "recent_jobs": recent_jobs,
        "recent_artifacts": recent_artifacts,
        "relevant_memory": relevant_memory,
        "latest_checkpoint": latest_checkpoint,
        "latest_ramble_capture": latest_ramble_capture,
    }


def get_project_now(project_id: str, user_message: str = ""):
    context = _fetch_project_context(project_id, user_message)

    objective = context["objective"]
    next_step = context["next_step"]
    blockers = context["blockers"]
    recent_messages = context["recent_messages"]
    recent_jobs = context["recent_jobs"]
    recent_artifacts = context["recent_artifacts"]
    relevant_memory = context["relevant_memory"]
    latest_checkpoint = context["latest_checkpoint"]
    latest_ramble_capture = context["latest_ramble_capture"]
    project_state = context["project_state"]

    objective_title = (objective or {}).get("title") or (project_state or {}).get("current_objective")
    next_step_title = (next_step or {}).get("title") or (project_state or {}).get("next_step")

    prioritized_actions = []
    if next_step_title:
        prioritized_actions.append(
            {
                "id": "execute_next_step",
                "priority": "high",
                "kind": "next_step",
                "title": next_step_title,
                "reason": "Resolved from persisted project state and next-step records.",
                "payload": {
                    "project_id": project_id,
                    "objective_id": (objective or {}).get("id"),
                    "next_step_id": (next_step or {}).get("id"),
                },
            }
        )

    if blockers:
        top_blocker = blockers[0]
        prioritized_actions.append(
            {
                "id": "resolve_blocker",
                "priority": "high",
                "kind": "blocker",
                "title": top_blocker.get("title"),
                "reason": "Open blockers exist in durable project state and should be resolved before advancing.",
                "payload": {"project_id": project_id, "blocker_id": top_blocker.get("id")},
            }
        )

    prioritized_actions.append(
        {
            "id": "capture_checkpoint",
            "priority": "medium",
            "kind": "checkpoint",
            "title": "Capture a fresh checkpoint",
            "reason": (
                "No durable checkpoint artifact exists yet."
                if latest_checkpoint is None
                else "Capture a new checkpoint after meaningful progress."
            ),
            "payload": {"project_id": project_id},
        }
    )

    if not relevant_memory:
        prioritized_actions.append(
            {
                "id": "strengthen_memory",
                "priority": "medium",
                "kind": "memory",
                "title": "Upsert a durable project memory",
                "reason": "No relevant durable memory surfaced for the active context.",
                "payload": {"project_id": project_id, "scope": "project"},
            }
        )

    prioritized_actions.append(
        {
            "id": "capture_ramble",
            "priority": "low",
            "kind": "ramble",
            "title": "Capture a freeform ramble input",
            "reason": "Ramble capture remains useful for extracting tasks, questions, and decisions.",
            "payload": {"project_id": project_id},
        }
    )

    top_blocker = blockers[0] if blockers else None

    return {
        "ok": True,
        "project_id": project_id,
        "project": {
            "id": context["project"].get("id"),
            "name": context["project"].get("name"),
            "status": context["project"].get("status"),
            "current_objective_id": context["project"].get("current_objective_id"),
            "meta": context["project"].get("meta") or {},
            "last_user_message": user_message,
        },
        "objective": {"id": (objective or {}).get("id"), "title": objective_title} if objective_title else None,
        "next_step": {"id": (next_step or {}).get("id"), "title": next_step_title} if next_step_title else None,
        "blockers": blockers,
        "recent_jobs": recent_jobs,
        "recent_artifacts": recent_artifacts,
        "recent_messages": recent_messages,
        "relevant_memory": relevant_memory,
        "latest_checkpoint": latest_checkpoint,
        "latest_ramble_capture": latest_ramble_capture,
        "operator": {
            "status": "blocked" if blockers else ("stable" if next_step_title else "forming"),
            "summary": (
                f"Objective: {objective_title or 'unresolved'} | "
                f"Next: {next_step_title or 'unresolved'} | "
                f"Memory: {len(relevant_memory)} signal(s)"
            ),
            "prioritized_actions": prioritized_actions,
            "workflow_chain": [a["title"] for a in prioritized_actions[:3]],
            "signals": {
                "open_blockers": len(blockers),
                "failed_jobs": len([j for j in recent_jobs if j.get("status") == "failed"]),
                "queued_jobs": len([j for j in recent_jobs if j.get("status") == "queued"]),
                "running_jobs": len([j for j in recent_jobs if j.get("status") == "running"]),
                "completed_jobs": len([j for j in recent_jobs if j.get("status") == "completed"]),
                "recent_messages": len(recent_messages),
                "memory_signals": len(relevant_memory),
                "checkpoint_present": latest_checkpoint is not None,
                "ramble_capture_present": latest_ramble_capture is not None,
            },
            "richer_summary": {
                "objective_title": objective_title,
                "next_step_title": next_step_title,
                "top_blocker": (top_blocker or {}).get("title"),
                "top_memory_titles": [m.get("title") for m in relevant_memory[:3]],
                "workflow_readiness": "ready" if next_step_title and not blockers else "forming",
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
                    "sequence_no": m.get("sequence_no"),
                }
                for m in recent_messages[-5:]
            ],
            "memory_signal_titles": [m.get("title") for m in relevant_memory[:5]],
            "latest_checkpoint_title": (latest_checkpoint or {}).get("title"),
            "latest_ramble_capture_title": (latest_ramble_capture or {}).get("title"),
        },
    }

