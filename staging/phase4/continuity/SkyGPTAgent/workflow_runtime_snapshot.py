
from pydantic import BaseModel, Field

class WorkflowRuntimeSnapshot(BaseModel):
    ok: bool = True
    workflow_id: str
    dry_run: bool = True
    status: str
    promotion_decision: str
    compiled_step_count: int = 0
    blocked_steps: list[str] = Field(default_factory=list)
    unsupported_kinds: list[str] = Field(default_factory=list)
    summary: str
    concise_report: list[str] = Field(default_factory=list)
