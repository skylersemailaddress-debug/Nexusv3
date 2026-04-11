from app.services.state_builder import get_project_now
from app.services.operator import build_operator_state


def _safe_title(item, default=None):
    if not item:
        return default
    return item.get("title", default)


def _message_preview(messages: list[dict], limit: int = 5) -> list[dict]:
    previews = []
    for message in messages[-limit:]:
        previews.append(
            {
                "id": message.get("id"),
                "role": message.get("role"),
                "content": message.get("content"),
                "created_at": message.get("created_at"),
            }
        )
    return previews


def build_brief(project_id: str) -> dict:
    now = get_project_now(project_id)

    if not now.get("ok"):
        return now

    objective = now.get("objective")
    next_step = now.get("next_step")
    blockers = now.get("blockers", [])
    recent_jobs = now.get("recent_jobs", [])
    recent_artifacts = now.get("recent_artifacts", [])
    relevant_memory = now.get("relevant_memory", [])
    recent_messages = now.get("recent_messages", [])

    latest_checkpoint = next(
        (artifact for artifact in recent_artifacts if artifact.get("kind") == "checkpoint"),
        None,
    )
    latest_ramble_capture = next(
        (artifact for artifact in recent_artifacts if artifact.get("kind") == "ramble_capture"),
        None,
    )

    operator_state = build_operator_state(now)

    return {
        "ok": True,
        "project_id": project_id,
        "where_we_left_off": {
            "objective": _safe_title(objective),
            "next_step": _safe_title(next_step),
            "open_blockers": len(blockers),
        },
        "what_changed": {
            "recent_jobs": len(recent_jobs),
            "recent_artifacts": len(recent_artifacts),
            "recent_messages": len(recent_messages),
            "memory_signals": len(relevant_memory),
        },
        "next_best_move": _safe_title(next_step),
        "blockers": blockers,
        "memory_signals": [_safe_title(item) for item in relevant_memory[:5]],
        "recent_message_preview": _message_preview(recent_messages, 5),
        "latest_checkpoint": _safe_title(latest_checkpoint),
        "latest_ramble_capture": _safe_title(latest_ramble_capture),
        "operator": operator_state,
    }


def build_context(project_id: str, user_message: str) -> dict:
    now = get_project_now(project_id, user_message)

    if not now.get("ok"):
        return now

    latest_checkpoint = next(
        (artifact for artifact in now.get("recent_artifacts", []) if artifact.get("kind") == "checkpoint"),
        None,
    )
    latest_ramble_capture = next(
        (artifact for artifact in now.get("recent_artifacts", []) if artifact.get("kind") == "ramble_capture"),
        None,
    )

    operator_state = build_operator_state(now)
    recent_messages = now.get("recent_messages", [])
    relevant_memory = now.get("relevant_memory", [])

    return {
        "ok": True,
        "project_id": project_id,
        "user_message": user_message,
        "project": now.get("project"),
        "objective": now.get("objective"),
        "next_step": now.get("next_step"),
        "blockers": now.get("blockers", []),
        "recent_jobs": now.get("recent_jobs", []),
        "recent_artifacts": now.get("recent_artifacts", []),
        "recent_messages": recent_messages,
        "relevant_memory": relevant_memory,
        "latest_checkpoint": latest_checkpoint,
        "latest_ramble_capture": latest_ramble_capture,
        "operator": operator_state,
        "next_suggested_actions": operator_state.get("prioritized_actions", []),
        "continuity": {
            "recent_message_count": len(recent_messages),
            "memory_signal_count": len(relevant_memory),
            "recent_message_preview": _message_preview(recent_messages, 5),
            "memory_signal_titles": [_safe_title(item) for item in relevant_memory[:5]],
            "latest_checkpoint_title": _safe_title(latest_checkpoint),
            "latest_ramble_capture_title": _safe_title(latest_ramble_capture),
        },
    }