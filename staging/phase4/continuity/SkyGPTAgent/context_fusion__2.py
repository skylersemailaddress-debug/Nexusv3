from copy import deepcopy


def _titleify(value):
    if value is None:
        return None
    if isinstance(value, dict):
        title = value.get("title") or value.get("name") or value.get("label")
        return str(title) if title else None
    return str(value)


def _merge_title(existing, title):
    if not title:
        return existing
    if existing is None:
        return {"title": title}
    if isinstance(existing, dict):
        merged = dict(existing)
        if not merged.get("title"):
            merged["title"] = title
        return merged
    return {"title": str(existing)}


def fuse_context_from_resume(project_id, context, resume_result=None):
    merged = deepcopy(context or {})
    try:
        if resume_result is None:
            from app.services.resume import build_resume
            resume_result = build_resume(project_id)
    except Exception:
        return merged

    if not isinstance(resume_result, dict) or not resume_result.get("ok"):
        return merged

    resume = resume_result.get("resume", {}) or {}
    objective_title = _titleify(resume.get("objective"))
    next_step_title = _titleify(resume.get("next_step"))

    merged["objective"] = _merge_title(merged.get("objective"), objective_title)
    merged["next_step"] = _merge_title(merged.get("next_step"), next_step_title)

    continuity = merged.get("continuity") or {}
    continuity["has_objective"] = bool(_titleify(merged.get("objective")))
    continuity["has_next_step"] = bool(_titleify(merged.get("next_step")))
    continuity.setdefault("status", "ready")
    merged["continuity"] = continuity

    if not merged.get("next_suggested_actions") and next_step_title:
        merged["next_suggested_actions"] = [next_step_title]

    if resume.get("recent_messages") and not merged.get("recent_messages"):
        merged["recent_messages"] = resume.get("recent_messages")

    if resume.get("memory_signals") and not merged.get("relevant_memory"):
        merged["relevant_memory"] = resume.get("memory_signals")

    return merged

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
