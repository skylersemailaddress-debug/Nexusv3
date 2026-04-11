from fastapi import APIRouter, Depends, HTTPException

from routes.auth_deps import get_current_user
from schemas.action_schema import ActionPayload
from services.job_service import (
    cancel_job,
    enqueue_action_job,
    enqueue_workflow_job,
    get_job,
    list_jobs_for_actor,
)
from services.observability_service import record_event

router = APIRouter()


@router.post("/runs/actions/test")
def run_action_test(payload: ActionPayload, user=Depends(get_current_user)):
    actor = {"username": user.username, "role": user.role}
    job = enqueue_action_job("test", actor, payload.model_dump())
    record_event("runs.actions.test.queued", actor=actor, detail={"job_id": job["id"]})
    return {"job": job, "actor": actor}


@router.post("/runs/actions/refresh")
def run_action_refresh(payload: ActionPayload, user=Depends(get_current_user)):
    actor = {"username": user.username, "role": user.role}
    job = enqueue_action_job("refresh", actor, payload.model_dump())
    record_event("runs.actions.refresh.queued", actor=actor, detail={"job_id": job["id"]})
    return {"job": job, "actor": actor}


@router.post("/runs/workflows/open-loops/{loop_id}/close")
def run_workflow_close(loop_id: str, user=Depends(get_current_user)):
    actor = {"username": user.username, "role": user.role}
    job = enqueue_workflow_job("close", actor, {"loop_id": loop_id})
    record_event("runs.workflows.open_loops.close.queued", actor=actor, detail={"job_id": job["id"], "loop_id": loop_id})
    return {"job": job, "actor": actor}


@router.post("/runs/workflows/open-loops/{loop_id}/reopen")
def run_workflow_reopen(loop_id: str, user=Depends(get_current_user)):
    actor = {"username": user.username, "role": user.role}
    job = enqueue_workflow_job("reopen", actor, {"loop_id": loop_id})
    record_event("runs.workflows.open_loops.reopen.queued", actor=actor, detail={"job_id": job["id"], "loop_id": loop_id})
    return {"job": job, "actor": actor}


@router.post("/runs/{job_id}/cancel")
def cancel_run(job_id: str, user=Depends(get_current_user)):
    actor = {"username": user.username, "role": user.role}
    job = cancel_job(job_id, actor)
    if job is None:
        raise HTTPException(status_code=404, detail="Runtime job not found")
    record_event("runs.cancel.requested", actor=actor, detail={"job_id": job_id, "status": job["status"]})
    return {"job": job, "actor": actor}


@router.get("/runs")
def list_runs(user=Depends(get_current_user)):
    actor = {"username": user.username, "role": user.role}
    jobs = list_jobs_for_actor(actor)
    record_event("runs.list.read", actor=actor, detail={"count": len(jobs)})
    return {"items": jobs, "count": len(jobs), "actor": actor}


@router.get("/runs/{job_id}")
def get_run(job_id: str, user=Depends(get_current_user)):
    actor = {"username": user.username, "role": user.role}
    job = get_job(job_id, actor)
    if job is None:
        raise HTTPException(status_code=404, detail="Runtime job not found")
    record_event("runs.detail.read", actor=actor, detail={"job_id": job_id, "status": job["status"]})
    return {"job": job, "actor": actor}
