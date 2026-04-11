from __future__ import annotations

from pydantic import BaseModel, Field


class WorkflowRuntimeHandoffBundle(BaseModel):
    ok: bool = True
    workflow_id: str
    dry_run: bool = True
    overall_status: str
    promotion_decision: str
    headline: str
    operator_summary: str
    risk_flags: list[str] = Field(default_factory=list)
    validation_notes: list[str] = Field(default_factory=list)
    compact_payload: dict = Field(default_factory=dict)
