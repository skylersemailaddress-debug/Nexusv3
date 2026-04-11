from __future__ import annotations

from pydantic import BaseModel, Field


class WorkflowRuntimeGatewayRequest(BaseModel):
    workflow_id: str
    steps: list[dict] = Field(default_factory=list)
    dry_run: bool = True
