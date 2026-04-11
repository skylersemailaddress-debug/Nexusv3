from app.services.state_builder import get_project_now


def build_canonical_context(
    *,
    project_id: str,
    base_context: dict | None,
    memory_search_fn=None,
    checkpoint_read_fn=None,
    user_message: str | None = None,
) -> dict:
    live = get_project_now(project_id, memory_query=user_message)

    context = dict(base_context or {})
    context.update(
        {
            "project_id": project_id,
            "live_context": live,
            "project": live.get("project"),
            "project_state": live.get("project_state"),
            "objective": live.get("objective"),
            "next_step": live.get("next_step"),
            "blockers": live.get("blockers") or [],
            "recent_messages": live.get("recent_messages") or [],
            "relevant_memory": live.get("relevant_memory") or [],
            "continuity": live.get("continuity") or {},
            "next_suggested_actions": live.get("next_suggested_actions") or [],
            "recent_writeback": live.get("recent_writeback"),
            "recent_jobs": live.get("recent_jobs") or [],
            "recent_artifacts": live.get("recent_artifacts") or [],
            "memory": live.get("relevant_memory") or [],
            "loop_state": {
                "objective": (live.get("objective") or {}).get("title"),
                "next_step": (live.get("next_step") or {}).get("title"),
                "has_open_blockers": bool(live.get("blockers")),
                "recent_message_count": len(live.get("recent_messages") or []),
                "memory_signal_count": len(live.get("relevant_memory") or []),
            },
        }
    )

    if user_message:
        context["user_message"] = user_message

    if memory_search_fn:
        try:
            extra_memory = memory_search_fn(project_id, user_message or "")
            if extra_memory:
                context["searched_memory"] = extra_memory
        except Exception:
            context["searched_memory"] = []

    if checkpoint_read_fn:
        try:
            checkpoint = checkpoint_read_fn(project_id)
            if checkpoint:
                context["checkpoint"] = checkpoint
        except Exception:
            context["checkpoint"] = None

    return context

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
