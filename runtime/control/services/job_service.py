import threading
import time
import uuid
from typing import Any

from services.actions_service import run_refresh_action, run_test_action
from services.env_service import get_runtime_config
from services.observability_service import audit_write, record_event
from services.workflow_service import close_open_loop, reopen_open_loop
from storage import (
    complete_runtime_job,
    create_runtime_job,
    list_runtime_jobs,
    mark_runtime_job_retrying,
    mark_runtime_job_running,
    mark_runtime_job_timed_out,
    read_runtime_job,
)


def _job_limits() -> tuple[int, int]:
    config = get_runtime_config()
    return int(config["job_default_timeout_seconds"]), int(config["job_max_retries"])


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


def _detect_stuck_jobs() -> None:
    now_ts = int(time.time())
    for job in list_runtime_jobs():
        if job["status"] != "running" or not job["started_at"]:
            continue
        timeout_seconds = max(int(job.get("timeout_seconds", 0)), 1)
        if int(job["started_at"]) + timeout_seconds > now_ts:
            continue
        error = f"Job exceeded timeout of {timeout_seconds}s"
        timed_out = mark_runtime_job_timed_out(job["id"], error, now_ts)
        if timed_out is None or timed_out["status"] != "timed_out":
            continue
        actor = {"username": job["requested_by"], "role": job["requested_role"]}
        audit_write(actor, "job.timed_out", {"job_id": job["id"], "job_type": job["job_type"], "job_name": job["job_name"]})
        record_event("job.timed_out", actor=actor, detail={"job_id": job["id"], "job_type": job["job_type"], "job_name": job["job_name"], "timeout_seconds": timeout_seconds}, status="error")


def _execute_once(job: dict[str, Any]) -> dict[str, Any]:
    if job["job_type"] == "action":
        return _run_action_job(job["job_name"], job["payload"])
    if job["job_type"] == "workflow":
        return _run_workflow_job(job["job_name"], job["payload"])
    raise ValueError(f"Unknown job type: {job['job_type']}")


def _execute_job(job: dict[str, Any]) -> None:
    actor = {"username": job["requested_by"], "role": job["requested_role"]}
    while True:
        running_job = mark_runtime_job_running(job["id"], int(time.time()))
        if running_job is None:
            return
        record_event("job.started", actor=actor, detail={"job_id": job["id"], "job_type": job["job_type"], "job_name": job["job_name"], "attempt": running_job["attempt"]})
        try:
            result = _execute_once(running_job)
            updated = complete_runtime_job(
                job["id"],
                status="succeeded",
                result=result,
                error=None,
                completed_at=int(time.time()),
            )
            if updated is None or updated["status"] != "succeeded":
                return
            audit_write(actor, "job.completed", {"job_id": job["id"], "job_type": job["job_type"], "job_name": job["job_name"], "attempt": updated["attempt"]})
            record_event("job.completed", actor=actor, detail={"job_id": job["id"], "job_type": job["job_type"], "job_name": job["job_name"], "attempt": updated["attempt"]})
            return
        except Exception as exc:
            current = read_runtime_job(job["id"])
            if current is None or current["status"] == "timed_out":
                return
            if current["attempt"] < current["max_attempts"]:
                retried = mark_runtime_job_retrying(job["id"], str(exc))
                audit_write(actor, "job.retrying", {"job_id": job["id"], "job_type": job["job_type"], "job_name": job["job_name"], "attempt": current["attempt"], "max_attempts": current["max_attempts"], "error": str(exc)})
                record_event("job.retrying", actor=actor, detail={"job_id": job["id"], "job_type": job["job_type"], "job_name": job["job_name"], "attempt": current["attempt"], "max_attempts": current["max_attempts"], "error": str(exc)})
                if retried is None:
                    return
                continue

            updated = complete_runtime_job(
                job["id"],
                status="failed",
                result=None,
                error=str(exc),
                completed_at=int(time.time()),
            )
            if updated is None:
                return
            audit_write(actor, "job.failed", {"job_id": job["id"], "job_type": job["job_type"], "job_name": job["job_name"], "attempt": current["attempt"], "max_attempts": current["max_attempts"], "error": str(exc)})
            record_event("job.failed", actor=actor, detail={"job_id": job["id"], "job_type": job["job_type"], "job_name": job["job_name"], "attempt": current["attempt"], "max_attempts": current["max_attempts"], "error": str(exc)}, status="error")
            return


def enqueue_job(
    *,
    job_type: str,
    job_name: str,
    actor: dict[str, str],
    payload: dict[str, Any],
) -> dict[str, Any]:
    timeout_seconds, max_retries = _job_limits()
    safe_max_attempts = max(1, min(max_retries, 3))
    job = create_runtime_job(
        str(uuid.uuid4()),
        job_type,
        job_name,
        actor["username"],
        actor["role"],
        payload,
        safe_max_attempts,
        timeout_seconds,
        int(time.time()),
    )
    audit_write(actor, "job.queued", {"job_id": job["id"], "job_type": job_type, "job_name": job_name, "max_attempts": safe_max_attempts, "timeout_seconds": timeout_seconds})
    record_event("job.queued", actor=actor, detail={"job_id": job["id"], "job_type": job_type, "job_name": job_name, "max_attempts": safe_max_attempts, "timeout_seconds": timeout_seconds})
    thread = threading.Thread(target=_execute_job, args=(job,), daemon=True)
    thread.start()
    return job


def enqueue_action_job(job_name: str, actor: dict[str, str], payload: dict[str, Any]) -> dict[str, Any]:
    return enqueue_job(job_type="action", job_name=job_name, actor=actor, payload=payload)


def enqueue_workflow_job(job_name: str, actor: dict[str, str], payload: dict[str, Any]) -> dict[str, Any]:
    return enqueue_job(job_type="workflow", job_name=job_name, actor=actor, payload=payload)


def get_job(job_id: str, actor: dict[str, str]) -> dict[str, Any] | None:
    _detect_stuck_jobs()
    job = read_runtime_job(job_id)
    if job is None:
        return None
    if actor["role"] != "admin" and job["requested_by"] != actor["username"]:
        return None
    return job


def list_jobs_for_actor(actor: dict[str, str]) -> list[dict[str, Any]]:
    _detect_stuck_jobs()
    jobs = list_runtime_jobs()
    if actor["role"] == "admin":
        return jobs
    return [job for job in jobs if job["requested_by"] == actor["username"]]
