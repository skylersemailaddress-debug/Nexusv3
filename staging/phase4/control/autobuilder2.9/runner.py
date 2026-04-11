from fastapi import APIRouter, Depends

from app.auth import require_runner_secret
from app.routes.jobs import claim_job_logic, complete_job_logic
from app.services.control_plane import record_runner_heartbeat, renew_runner_leases

router = APIRouter(prefix="/runner", tags=["runner"])


@router.post("/claim", dependencies=[Depends(require_runner_secret)])
def claim_job(body: dict):
    return claim_job_logic(body)


@router.post("/complete", dependencies=[Depends(require_runner_secret)])
def complete_job(body: dict):
    return complete_job_logic(body)


@router.post("/heartbeat", dependencies=[Depends(require_runner_secret)])
def runner_heartbeat(body: dict):
    runner_id = body.get("runner_id")
    if not runner_id:
        return {"ok": False, "error": "Missing runner_id"}
    active_job_ids = body.get("active_job_ids") or []
    if not active_job_ids and body.get("job_id"):
        active_job_ids = [body["job_id"]]
    heartbeat = record_runner_heartbeat(
        runner_id,
        status=body.get("status") or "idle",
        project_id=body.get("project_id"),
        job_id=body.get("job_id"),
        capabilities=body.get("capabilities") or [],
        max_concurrency=body.get("max_concurrency"),
        meta={"source": "runner.heartbeat"},
    )
    leases = renew_runner_leases(runner_id, active_job_ids)
    return {"ok": True, "runner": heartbeat, "leases": leases}
