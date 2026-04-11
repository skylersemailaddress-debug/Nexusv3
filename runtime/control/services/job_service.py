import threading
import time
import uuid
from typing import Any

from services.actions_service import run_refresh_action, run_test_action
from services.observability_service import audit_write, record_event
from services.workflow_service import close_open_loop, reopen_open_loop
from storage import (
    complete_runtime_job,
    create_runtime_job,
    list_runtime_jobs,
    mark_runtime_job_running,
    read_runtime_job,
)


def _run_action_job(job_name: str, payload: dict[str, Any]) -> dict[str, Any]:
    if job_name == "test":
        return run_test_action(payload)
    if job_name == "refresh":
        return run_refresh_action(payload)
    raise ValueError(f"Unknown action job: {job_name}")


def _run_workflow_job(job_name: str, payload: dict[str, Any]) -> dict[str, Any]:
    loop_id = str(payload["loop_id"])
    if job_name == "close":
        item = close_open_loop(loop_id)
    elif job_name == "reopen":
        item = reopen_open_loop(loop_id)
    else:
        raise ValueError(f"Unknown workflow job: {job_name}")
    if item is None:
        raise ValueError("Open loop not found")
    return {"item": item}


def _execute_job(job: dict[str, Any]) -> None:
    mark_runtime_job_running(job["id"], int(time.time()))
    actor = {"username": job["requested_by"], "role": job["requested_role"]}
    record_event("job.started", actor=actor, detail={"job_id": job["id"], "job_type": job["job_type"], "job_name": job["job_name"]})
    try:
        if job["job_type"] == "action":
            result = _run_action_job(job["job_name"], job["payload"])
        elif job["job_type"] == "workflow":
            result = _run_workflow_job(job["job_name"], job["payload"])
        else:
            raise ValueError(f"Unknown job type: {job['job_type']}")

        complete_runtime_job(
            job["id"],
            status="succeeded",
            result=result,
            error=None,
            completed_at=int(time.time()),
        )
        audit_write(actor, "job.completed", {"job_id": job["id"], "job_type": job["job_type"], "job_name": job["job_name"]})
        record_event("job.completed", actor=actor, detail={"job_id": job["id"], "job_type": job["job_type"], "job_name": job["job_name"]})
    except Exception as exc:
        complete_runtime_job(
            job["id"],
            status="failed",
            result=None,
            error=str(exc),
            completed_at=int(time.time()),
        )
        audit_write(actor, "job.failed", {"job_id": job["id"], "job_type": job["job_type"], "job_name": job["job_name"], "error": str(exc)})
        record_event("job.failed", actor=actor, detail={"job_id": job["id"], "job_type": job["job_type"], "job_name": job["job_name"], "error": str(exc)}, status="error")


def enqueue_job(
    *,
    job_type: str,
    job_name: str,
    actor: dict[str, str],
    payload: dict[str, Any],
) -> dict[str, Any]:
    job = create_runtime_job(
        str(uuid.uuid4()),
        job_type,
        job_name,
        actor["username"],
        actor["role"],
        payload,
        int(time.time()),
    )
    audit_write(actor, "job.queued", {"job_id": job["id"], "job_type": job_type, "job_name": job_name})
    record_event("job.queued", actor=actor, detail={"job_id": job["id"], "job_type": job_type, "job_name": job_name})
    thread = threading.Thread(target=_execute_job, args=(job,), daemon=True)
    thread.start()
    return job


def enqueue_action_job(job_name: str, actor: dict[str, str], payload: dict[str, Any]) -> dict[str, Any]:
    return enqueue_job(job_type="action", job_name=job_name, actor=actor, payload=payload)


def enqueue_workflow_job(job_name: str, actor: dict[str, str], payload: dict[str, Any]) -> dict[str, Any]:
    return enqueue_job(job_type="workflow", job_name=job_name, actor=actor, payload=payload)


def get_job(job_id: str, actor: dict[str, str]) -> dict[str, Any] | None:
    job = read_runtime_job(job_id)
    if job is None:
        return None
    if actor["role"] != "admin" and job["requested_by"] != actor["username"]:
        return None
    return job


def list_jobs_for_actor(actor: dict[str, str]) -> list[dict[str, Any]]:
    jobs = list_runtime_jobs()
    if actor["role"] == "admin":
        return jobs
    return [job for job in jobs if job["requested_by"] == actor["username"]]
