from fastapi import APIRouter, Depends
from app.auth import require_api_token
from app.services.state_builder import get_project_now

router = APIRouter(
    prefix="/projects",
    tags=["projects"],
    dependencies=[Depends(require_api_token)],
)

def _short(x):
    if not x:
        return ""
    return x[:150] + ("..." if len(x) > 150 else "")

@router.get("/{project_id}/resume")
def project_resume(project_id: str):
    ctx = get_project_now(project_id)

    msgs = ctx.get("recent_messages", [])
    mem = ctx.get("relevant_memory", [])
    obj = ctx.get("objective")
    step = ctx.get("next_step")
    suggestions = ctx.get("next_suggested_actions", [])

    next_best_move = suggestions[0] if suggestions else (step["title"] if step else "")

    return {
        "ok": True,
        "project_id": project_id,
        "resume": {
            "objective": obj["title"] if obj else None,
            "next_step": step["title"] if step else None,
            "recent_message_count": len(msgs),
            "memory_signal_count": len(mem),
            "recent_messages": [
                {"role": m["role"], "content": _short(m["content"])}
                for m in msgs
            ],
        },
        "brief": {
            "where_we_left_off": f"{obj['title']} -> {step['title']}" if obj and step else "",
            "next_best_move": next_best_move,
            "memory_signals": [m["title"] for m in mem],
            "suggested_actions": suggestions,
        },
        "context": ctx,
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
