from __future__ import annotations

from pydantic import BaseModel, Field


class WorkflowRuntimeExecutiveSummary(BaseModel):
    ok: bool = True
    workflow_id: str
    dry_run: bool = True
    overall_status: str
    promotion_decision: str
    executive_title: str
    executive_summary: str
    risk_flags: list[str] = Field(default_factory=list)
    recommended_next_move: str
    compact_payload: dict = Field(default_factory=dict)
