from app.db import get_conn


def _clean_message(row: dict) -> dict:
    return {
        "id": row.get("id"),
        "role": row.get("role"),
        "content": row.get("content"),
        "meta": row.get("meta") or {},
        "sequence_no": row.get("sequence_no"),
        "created_at": row.get("created_at"),
    }


def _clean_memory(row: dict) -> dict:
    return {
        "id": row.get("id"),
        "scope": row.get("scope"),
        "title": row.get("title"),
        "content": row.get("content"),
        "status": row.get("status"),
        "confidence": row.get("confidence"),
        "meta": row.get("meta") or {},
        "updated_at": row.get("updated_at"),
    }


def _hydrate_title(row: dict | None, fallback_title: str | None) -> dict | None:
    title = (fallback_title or "").strip()
    if row and row.get("title"):
        return row
    if title:
        hydrated = dict(row or {})
        hydrated["title"] = title
        return hydrated
    return row


def _derive_next_actions(project, objective, next_step, blockers, relevant_memory):
    actions = []

    open_blocker_titles = [b.get("title") for b in blockers if b.get("title")]
    if open_blocker_titles:
        actions.append(f"Resolve blocker: {open_blocker_titles[0]}")

    memory_priority = []
    for mem in relevant_memory:
        title = (mem.get("title") or "").lower()
        content = mem.get("content") or ""
        if any(token in title for token in ["next hardening priority", "current objective", "continuity spine status"]):
            memory_priority.append(content)

    for item in memory_priority:
        if item and item not in actions:
            actions.append(item)

    if next_step and next_step.get("title"):
        step_title = next_step["title"]
        if step_title not in actions:
            actions.append(step_title)

    if objective and objective.get("title") and not next_step:
        actions.append(f"Define next step for objective: {objective['title']}")

    if not objective:
        actions.append("Set or create a current objective.")

    if not relevant_memory:
        actions.append("Add durable memory records for project recall.")

    deduped = []
    seen = set()
    for item in actions:
        key = item.strip().lower()
        if key and key not in seen:
            deduped.append(item)
            seen.add(key)

    return deduped[:5]


def get_project_now(project_id: str, memory_query: str | None = None) -> dict:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("select * from projects where id = %s", (project_id,))
        project = cur.fetchone()
        if not project:
            return {"ok": False, "error": f"Project not found: {project_id}"}

        cur.execute("select * from project_state where project_id = %s", (project_id,))
        project_state = cur.fetchone()

        structured_state = (project_state or {}).get("structured_state") or {}

        fallback_objective_title = (
            structured_state.get("current_objective")
            or (project_state or {}).get("current_objective")
            or ""
        )
        fallback_next_step_title = (
            structured_state.get("next_step")
            or (project_state or {}).get("next_step")
            or ""
        )

        objective_id = project.get("current_objective_id") or structured_state.get("current_objective_id")

        objective = None
        if objective_id:
            cur.execute("select * from objectives where id = %s", (objective_id,))
            objective = cur.fetchone()
        objective = _hydrate_title(objective, fallback_objective_title)

        next_step_id = (objective or {}).get("next_step_id") or structured_state.get("next_step_id")

        next_step = None
        if next_step_id:
            cur.execute("select * from next_steps where id = %s", (next_step_id,))
            next_step = cur.fetchone()
        next_step = _hydrate_title(next_step, fallback_next_step_title)

        blocker_ids_open = structured_state.get("blocker_ids_open") or []
        if blocker_ids_open:
            cur.execute(
                """
                select *
                from blockers
                where project_id = %s
                  and status = 'open'
                  and id = any(%s)
                order by created_at desc
                """,
                (project_id, blocker_ids_open),
            )
        else:
            cur.execute(
                """
                select *
                from blockers
                where project_id = %s and status = 'open'
                order by created_at desc
                """,
                (project_id,),
            )
        blockers = cur.fetchall()

        cur.execute("select * from jobs where project_id = %s order by created_at desc limit 10", (project_id,))
        jobs = cur.fetchall()

        cur.execute(
            """
            select *
            from artifacts
            where project_id = %s
              and kind in ('execution_result', 'execution_error')
            order by created_at desc
            limit 1
            """,
            (project_id,),
        )
        recent_writeback_artifact = cur.fetchone()

        cur.execute("select * from artifacts where project_id = %s order by created_at desc limit 10", (project_id,))
        artifacts = cur.fetchall()

        recent_writeback = None
        if recent_writeback_artifact:
            kind = recent_writeback_artifact.get("kind")
            meta = recent_writeback_artifact.get("meta") or {}
            payload = recent_writeback_artifact.get("payload") or {}
            if kind == "execution_result":
                summary = (payload.get("stdout") or "Execution completed").strip()
            else:
                summary = (payload.get("stderr") or "Execution failed").strip()
            recent_writeback = {
                "type": kind,
                "id": recent_writeback_artifact.get("id"),
                "job_id": meta.get("job_id") or payload.get("job_id"),
                "project_id": recent_writeback_artifact.get("project_id"),
                "summary": summary[:200] if isinstance(summary, str) else summary,
                "created_at": recent_writeback_artifact.get("created_at"),
            }

        cur.execute(
            """
            select id, role, content_text as content, meta, sequence_no, created_at
            from messages
            where project_id = %s
            order by sequence_no desc
            limit 10
            """,
            (project_id,),
        )
        messages = list(reversed([_clean_message(r) for r in cur.fetchall()]))

        if memory_query:
            cur.execute(
                """
                select *
                from memory_records
                where status = 'active'
                  and (project_id = %s or project_id is null)
                  and (title ilike %s or content ilike %s)
                order by confidence desc, updated_at desc
                limit 5
                """,
                (project_id, f"%{memory_query}%", f"%{memory_query}%"),
            )
            memory = [_clean_memory(r) for r in cur.fetchall()]
        else:
            memory = []

        if not memory:
            cur.execute(
                """
                select *
                from memory_records
                where status = 'active'
                  and (project_id = %s or project_id is null)
                order by confidence desc, updated_at desc
                limit 5
                """,
                (project_id,),
            )
            memory = [_clean_memory(r) for r in cur.fetchall()]

        next_suggested_actions = _derive_next_actions(project, objective, next_step, blockers, memory)
        continuity = {
            "status": "ready",
            "recent_message_count": len(messages),
            "memory_signal_count": len(memory),
            "has_objective": bool(objective and objective.get("title")),
            "has_next_step": bool(next_step and next_step.get("title")),
            "has_open_blockers": bool(blockers),
        }

        return {
            "ok": True,
            "project": project,
            "project_state": project_state,
            "objective": objective,
            "next_step": next_step,
            "blockers": blockers,
            "recent_jobs": jobs,
            "recent_artifacts": artifacts,
            "recent_writeback": recent_writeback,
            "recent_messages": messages,
            "relevant_memory": memory,
            "continuity": continuity,
            "next_suggested_actions": next_suggested_actions,
        }

# SKYGPT UNIVERSAL CONTEXT FUSION WRAPPER
from app.services.context_fusion import fuse_context_from_resume


def _skygpt_call_with_compatible_args(fn, project_id, input=None, inputs=None, **kwargs):
    attempts = [
        lambda: fn(project_id, input=input, inputs=inputs, **kwargs),
        lambda: fn(project_id, input=input, **kwargs),
        lambda: fn(project_id, inputs=inputs, **kwargs),
        lambda: fn(project_id, **kwargs),
        lambda: fn(project_id),
    ]
    last_error = None
    for attempt in attempts:
        try:
            return attempt()
        except TypeError as exc:
            last_error = exc
            continue
    if last_error is not None:
        raise last_error
    return fn(project_id)


def _skygpt_wrap_context_builder(fn):
    def _wrapped(project_id, input=None, inputs=None, **kwargs):
        result = _skygpt_call_with_compatible_args(fn, project_id, input=input, inputs=inputs, **kwargs)
        return fuse_context_from_resume(project_id, result)
    return _wrapped

try:
    _skygpt_original_run = run
    if callable(_skygpt_original_run):
        run = _skygpt_wrap_context_builder(_skygpt_original_run)
except NameError:
    pass

try:
    _skygpt_original_execute = execute
    if callable(_skygpt_original_execute):
        execute = _skygpt_wrap_context_builder(_skygpt_original_execute)
except NameError:
    pass

try:
    _skygpt_original_build_context = build_context
    if callable(_skygpt_original_build_context):
        build_context = _skygpt_wrap_context_builder(_skygpt_original_build_context)
except NameError:
    pass

try:
    _skygpt_original_build = build
    if callable(_skygpt_original_build):
        build = _skygpt_wrap_context_builder(_skygpt_original_build)
except NameError:
    pass
