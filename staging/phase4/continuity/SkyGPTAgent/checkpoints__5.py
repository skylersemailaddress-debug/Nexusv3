from datetime import datetime, timezone


def _clean_text(value) -> str:
    if value is None:
        return ""
    return " ".join(str(value).strip().split())


def build_compressed_project_summary(context: dict) -> str:
    context = context or {}

    objective = context.get("current_objective") or {}
    next_step = context.get("next_step") or {}
    recent_writeback = context.get("recent_writeback") or {}
    blockers = context.get("open_blockers") or []

    objective_title = _clean_text(objective.get("title") or objective.get("name"))
    next_step_title = _clean_text(next_step.get("title") or next_step.get("name"))
    writeback_summary = _clean_text(recent_writeback.get("summary"))
    blocker_count = len(blockers)

    parts = []

    if objective_title:
        parts.append(f"Objective: {objective_title}.")
    if next_step_title:
        parts.append(f"Next step: {next_step_title}.")
    if writeback_summary:
        parts.append(f"Recent execution: {writeback_summary}.")
    parts.append(f"Open blockers: {blocker_count}.")

    return " ".join(parts).strip()


def build_checkpoint_payload(project_id: str, context: dict, created_at: str | None = None) -> dict:
    context = context or {}

    current_objective = context.get("current_objective") or {}
    next_step = context.get("next_step") or {}
    recent_writeback = context.get("recent_writeback") or {}
    open_blockers = context.get("open_blockers") or []

    created_at = created_at or datetime.now(timezone.utc).isoformat()
    compressed_summary = build_compressed_project_summary(context)

    return {
        "project_id": project_id,
        "kind": "project_checkpoint",
        "created_at": created_at,
        "objective_id": current_objective.get("id"),
        "next_step_id": next_step.get("id"),
        "recent_writeback_id": recent_writeback.get("id"),
        "compressed_summary": compressed_summary,
        "meta": {
            "recent_writeback_type": recent_writeback.get("type"),
            "open_blocker_count": len(open_blockers),
        },
    }


def persist_checkpoint(checkpoint_upsert_fn, project_id: str, context: dict, created_at: str | None = None):
    payload = build_checkpoint_payload(project_id, context, created_at=created_at)
    return checkpoint_upsert_fn(payload)


def get_latest_checkpoint(checkpoint_read_fn, project_id: str):
    result = checkpoint_read_fn(project_id)
    if not result:
        return None
    if isinstance(result, list):
        return result[0] if result else None
    return result


def hydrate_context_from_checkpoint(context: dict, checkpoint: dict) -> dict:
    """
    Merge checkpoint data into context safely.
    Canonical rule: checkpoint fills gaps, never overrides fresh runtime data.
    """
    if not checkpoint:
        return context

    context = context or {}

    if not context.get("current_objective") and checkpoint.get("objective_id"):
        context["current_objective"] = {"id": checkpoint.get("objective_id")}

    if not context.get("next_step") and checkpoint.get("next_step_id"):
        context["next_step"] = {"id": checkpoint.get("next_step_id")}

    if not context.get("recent_writeback") and checkpoint.get("recent_writeback_id"):
        context["recent_writeback"] = {
            "id": checkpoint.get("recent_writeback_id"),
            "type": checkpoint.get("meta", {}).get("recent_writeback_type"),
        }

    if checkpoint.get("compressed_summary"):
        context["checkpoint_summary"] = checkpoint["compressed_summary"]

    return context


def create_checkpoint(project_id: str) -> dict:
    """
    Canonical route-facing checkpoint contract.

    routes/checkpoints.py expects:
        create_checkpoint(project_id)
    """
    payload = build_checkpoint_payload(project_id, {})
    return {
        "ok": True,
        "project_id": project_id,
        "checkpoint": payload,
    }
