from __future__ import annotations

from pydantic import BaseModel, Field


class WorkflowAdapter(BaseModel):
    kind: str
    adapter_name: str
    enabled: bool = True
    supports_dry_run: bool = True
    execution_mode: str = "deferred"
    notes: list[str] = Field(default_factory=list)


class WorkflowAdapterResolution(BaseModel):
    ok: bool = True
    requested_kinds: list[str] = Field(default_factory=list)
    resolved: list[WorkflowAdapter] = Field(default_factory=list)
    unsupported: list[str] = Field(default_factory=list)
