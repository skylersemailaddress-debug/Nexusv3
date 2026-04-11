from __future__ import annotations

from pydantic import BaseModel, Field


class WorkflowPromotionDecision(BaseModel):
    ok: bool = True
    workflow_id: str
    decision: str
    promotable: bool = False
    requires_review: bool = True
    reasons: list[str] = Field(default_factory=list)
    blocked_steps: list[str] = Field(default_factory=list)
    unsupported_kinds: list[str] = Field(default_factory=list)
    next_suggested_actions: list[str] = Field(default_factory=list)
    summary: str

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
