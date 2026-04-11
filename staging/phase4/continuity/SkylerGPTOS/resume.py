from fastapi import APIRouter, Depends
from app.auth import require_api_token
from app.services.briefing import build_brief, build_context

router = APIRouter(
    prefix="/projects",
    tags=["projects"],
    dependencies=[Depends(require_api_token)],
)


def _safe_title(item, default=None):
    if not item:
        return default
    return item.get("title", default)


@router.get("/{project_id}/resume")
def project_resume(project_id: str):
    brief = build_brief(project_id)
    if not brief.get("ok"):
        return brief

    context = build_context(project_id, "resume project state")
    if not context.get("ok"):
        return context

    recent_messages = context.get("recent_messages", [])
    relevant_memory = context.get("relevant_memory", [])
    blockers = context.get("blockers", [])

    return {
        "ok": True,
        "project_id": project_id,
        "resume": {
            "objective": _safe_title(context.get("objective")),
            "next_step": _safe_title(context.get("next_step")),
            "open_blockers": len(blockers),
            "recent_message_count": len(recent_messages),
            "memory_signal_count": len(relevant_memory),
            "memory_signal_titles": [item.get("title") for item in relevant_memory[:5]],
            "recent_messages": [
                {
                    "id": item.get("id"),
                    "role": item.get("role"),
                    "content": item.get("content"),
                    "created_at": item.get("created_at"),
                }
                for item in recent_messages[-5:]
            ],
            "latest_checkpoint": (context.get("latest_checkpoint") or {}).get("title"),
            "latest_ramble_capture": (context.get("latest_ramble_capture") or {}).get("title"),
            "continuity_status": "ready" if recent_messages or relevant_memory else "cold",
        },
        "brief": brief,
        "context": context,
    }