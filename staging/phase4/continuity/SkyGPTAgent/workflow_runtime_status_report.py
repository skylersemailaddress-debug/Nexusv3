from __future__ import annotations

from pydantic import BaseModel, Field


class WorkflowRuntimeStatusReport(BaseModel):
    ok: bool = True
    workflow_id: str
    dry_run: bool = True
    overall_status: str
    promotion_decision: str
    compiled_step_count: int = 0
    blocked_steps: list[str] = Field(default_factory=list)
    unsupported_kinds: list[str] = Field(default_factory=list)
    headline: str
    details: list[str] = Field(default_factory=list)
