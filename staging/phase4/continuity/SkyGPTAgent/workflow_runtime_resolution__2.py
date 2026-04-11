from __future__ import annotations

from pydantic import BaseModel, Field


class WorkflowResolvedStep(BaseModel):
    step_id: str
    kind: str
    target: str
    action: str
    adapter_name: str | None = None
    adapter_enabled: bool = False
    supported: bool = False
    blocked: bool = False
    reason: str | None = None


class WorkflowRuntimeResolution(BaseModel):
    ok: bool = True
    workflow_id: str
    dry_run: bool = True
    status: str
    resolved_steps: list[WorkflowResolvedStep] = Field(default_factory=list)
    unsupported_kinds: list[str] = Field(default_factory=list)
    blocked_steps: list[str] = Field(default_factory=list)
    summary: str
