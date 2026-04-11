
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Any

from app.auth import require_api_token
from app.services.briefing import build_context, build_brief
from app.services.devtools import (
    apply_generated_code,
    enqueue_generated_validation,
    evaluate_job_result,
    generate_code_packet,
    retry_job_step,
)

router = APIRouter(prefix="/orchestrate", tags=["orchestrate"], dependencies=[Depends(require_api_token)])

class OrchestrateActionRequest(BaseModel):
    capability_id: str
    project_id: str
    inputs: dict[str, Any] = Field(default_factory=dict)

@router.post("/action")
def orchestrate_action(req: OrchestrateActionRequest):
    if req.capability_id == "state.build_context":
        data = build_context(req.project_id, req.inputs.get("user_message", ""))
        summary = "Built project context."
    elif req.capability_id == "operator.plan":
        data = build_brief(req.project_id)
        summary = "Built operator plan."
    elif req.capability_id == "dev.generate_code":
        data = generate_code_packet(req.project_id, req.inputs.get("task", ""), req.inputs.get("target_paths") or [], req.inputs.get("acceptance_criteria") or [], approval_mode=req.inputs.get("approval_mode", "suggest_only"))
        summary = "Built development packet."
    elif req.capability_id == "dev.apply_patch":
        artifact_id = req.inputs.get("artifact_id")
        if not artifact_id:
            raise HTTPException(status_code=400, detail="artifact_id is required")
        data = apply_generated_code(req.project_id, artifact_id, req.inputs.get("requested_by"), req.inputs.get("approval_mode", "manual"), req.inputs.get("create_backup", True))
        summary = "Applied generated patch."
    elif req.capability_id == "dev.run_test":
        artifact_id = req.inputs.get("artifact_id")
        command = req.inputs.get("command")
        if not artifact_id or not command:
            raise HTTPException(status_code=400, detail="artifact_id and command are required")
        data = enqueue_generated_validation(req.project_id, artifact_id, command, req.inputs.get("requested_by"), req.inputs.get("approval_mode", "auto_read"))
        summary = "Queued validation command."
    elif req.capability_id == "dev.evaluate_result":
        job_id = req.inputs.get("job_id")
        if not job_id:
            raise HTTPException(status_code=400, detail="job_id is required")
        data = evaluate_job_result(job_id)
        summary = "Evaluated job result."
    elif req.capability_id == "dev.retry_step":
        job_id = req.inputs.get("job_id")
        if not job_id:
            raise HTTPException(status_code=400, detail="job_id is required")
        data = retry_job_step(job_id, req.inputs.get("requested_by"))
        summary = "Retried developer job."
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported capability_id: {req.capability_id}")
    return {
        "ok": True,
        "action_id": None,
        "capability_id": req.capability_id,
        "summary": summary,
        "status": "completed",
        "data": data,
        "artifacts": [],
        "logs": [],
        "events": [],
        "state_updates": {},
        "next_suggested_actions": data.get("next_suggested_actions", data.get("operator", {}).get("prioritized_actions", [])),
        "error": None,
    }
