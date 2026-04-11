from fastapi import APIRouter, Depends, Query

from app.auth import require_api_token
from app.db import get_conn

router = APIRouter(prefix="/system", tags=["system"], dependencies=[Depends(require_api_token)])


@router.get("/state")
def get_system_state(limit: int = Query(default=20, ge=1, le=100)):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            select
              count(*) filter (where status = 'queued') as queued,
              count(*) filter (where status = 'running') as running,
              count(*) filter (where status = 'failed') as failed,
              count(*) filter (where status = 'completed' and updated_at >= now() - interval '24 hours') as completed_recent_24h,
              count(*) filter (where updated_at >= now() - interval '24 hours' and error ilike 'Recovered stale running job%%') as recovered_recent_24h,
              count(*) filter (where status = 'queued' and coalesce((inputs->>'attempt_count')::int, 0) > 0 and updated_at >= now() - interval '24 hours') as retried_recent_24h
            from jobs
            """
        )
        queue = cur.fetchone()

        cur.execute(
            """
            select id, project_id, capability_id, status, claimed_by, inputs, error, updated_at
            from jobs
            order by updated_at desc nulls last, created_at desc
            limit %s
            """,
            (limit,),
        )
        jobs = cur.fetchall()

    recent_jobs = []
    for job in jobs:
        inputs = job.get("inputs") or {}
        autocode = inputs.get("autocode") or {}
        recent_jobs.append(
            {
                "id": job["id"],
                "project_id": job.get("project_id"),
                "capability_id": job.get("capability_id"),
                "status": job.get("status"),
                "claimed_by": job.get("claimed_by"),
                "attempt_count": int(inputs.get("attempt_count") or 0),
                "max_attempts": int(inputs.get("max_attempts") or 0),
                "auto_debug_attempts": int(autocode.get("auto_debug_attempts") or 0),
                "recovered": isinstance(job.get("error"), str) and job["error"].startswith("Recovered stale running job"),
                "retried": int(inputs.get("attempt_count") or 0) > 0,
                "error_summary": (job.get("error") or "")[:200] or None,
                "artifact_ids": [f"artifact-job-{job['id']}"],
                "updated_at": job.get("updated_at"),
            }
        )

    return {
        "ok": True,
        "queue": queue,
        "controls": {"global_pause": False, "project_pauses": []},
        "recent_jobs": recent_jobs,
    }


@router.get("/jobs/recent")
def get_recent_jobs(
    limit: int = Query(default=50, ge=1, le=200),
    project_id: str | None = None,
    status: str | None = None,
):
    clauses = []
    params: list[object] = []
    if project_id:
        clauses.append("project_id = %s")
        params.append(project_id)
    if status:
        clauses.append("status = %s")
        params.append(status)
    where = f"where {' and '.join(clauses)}" if clauses else ""

    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            f"""
            select id, project_id, capability_id, status, claimed_by, inputs, error, result, created_at, updated_at
            from jobs
            {where}
            order by updated_at desc nulls last, created_at desc
            limit %s
            """,
            (*params, limit),
        )
        items = cur.fetchall()

    response_items = []
    for job in items:
        inputs = job.get("inputs") or {}
        autocode = inputs.get("autocode") or {}
        response_items.append(
            {
                "id": job["id"],
                "project_id": job.get("project_id"),
                "capability_id": job.get("capability_id"),
                "status": job.get("status"),
                "claimed_by": job.get("claimed_by"),
                "attempt_count": int(inputs.get("attempt_count") or 0),
                "max_attempts": int(inputs.get("max_attempts") or 0),
                "recovered": isinstance(job.get("error"), str) and job["error"].startswith("Recovered stale running job"),
                "retried": int(inputs.get("attempt_count") or 0) > 0,
                "auto_debug_attempts": int(autocode.get("auto_debug_attempts") or 0),
                "error_summary": (job.get("error") or "")[:200] or None,
                "result_summary": ((job.get("result") or {}).get("stdout") or "")[:200] or None,
                "artifact_summary": [{"id": f"artifact-job-{job['id']}", "kind": "job_result", "title": f"Job result: {job['id']}"}],
                "created_at": job.get("created_at"),
                "updated_at": job.get("updated_at"),
            }
        )
    return {"ok": True, "items": response_items, "next_cursor": None}


@router.get("/failures/recent")
def get_recent_failures(
    limit: int = Query(default=50, ge=1, le=200),
    project_id: str | None = None,
    include_resolved: bool = Query(default=True),
):
    clauses = ["status = 'failed'"]
    params: list[object] = []
    if project_id:
        clauses.append("project_id = %s")
        params.append(project_id)
    where = f"where {' and '.join(clauses)}"
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            f"""
            select id, project_id, capability_id, status, inputs, error, updated_at
            from jobs
            {where}
            order by updated_at desc nulls last, created_at desc
            limit %s
            """,
            (*params, limit),
        )
        items = cur.fetchall()
    response_items = []
    for job in items:
        inputs = job.get("inputs") or {}
        autocode = inputs.get("autocode") or {}
        response_items.append(
            {
                "job_id": job["id"],
                "project_id": job.get("project_id"),
                "capability_id": job.get("capability_id"),
                "failure_class": "retryable_debug" if job.get("capability_id") in {"dev.run-test", "dev.run-lint", "dev.run-script", "local.powershell"} else "non_debuggable",
                "error_summary": (job.get("error") or "")[:200],
                "retried": int(inputs.get("attempt_count") or 0) > 0,
                "recovered": isinstance(job.get("error"), str) and job["error"].startswith("Recovered stale running job"),
                "auto_debug_triggered": int(autocode.get("auto_debug_attempts") or 0) > 0,
                "auto_debug_hard_stopped": False,
                "resolved": include_resolved and job.get("status") != "failed",
                "latest_status": job.get("status"),
                "updated_at": job.get("updated_at"),
            }
        )
    return {"ok": True, "items": response_items, "next_cursor": None}
