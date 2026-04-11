from __future__ import annotations

from pydantic import BaseModel, Field


class WorkflowRuntimeOperatorBrief(BaseModel):
    ok: bool = True
    workflow_id: str
    dry_run: bool = True
    overall_status: str
    promotion_decision: str
    brief_title: str
    brief_summary: str
    action_items: list[str] = Field(default_factory=list)
    risk_flags: list[str] = Field(default_factory=list)
    compact_payload: dict = Field(default_factory=dict)
