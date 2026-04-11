from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from psycopg.types.json import Json
from app.auth import require_api_token, require_runner_secret
from app.db import get_conn

router = APIRouter(tags=["jobs"])


class EnqueueJobRequest(BaseModel):
    id: str
    project_id: str | None = None
    objective_id: str | None = None
    capability_id: str
    approval_mode: str = "auto_read"
    risk_level: str = "low"
    inputs: dict = Field(default_factory=dict)
    requested_by: str | None = None


class ClaimJobRequest(BaseModel):
    runner_id: str


class CompleteJobRequest(BaseModel):
    job_id: str
    status: str
    result: dict | None = None
    error: str | None = None


@router.post("/jobs/enqueue", dependencies=[Depends(require_api_token)])
def enqueue_job(req: EnqueueJobRequest):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            '''
            insert into jobs (
                id, project_id, objective_id, capability_id, status,
                approval_mode, risk_level, inputs, requested_by
            )
            values (%s, %s, %s, %s, 'queued', %s, %s, %s, %s)
            returning id, project_id, objective_id, capability_id, status,
                      approval_mode, risk_level, inputs, requested_by, created_at
            ''',
            (
                req.id,
                req.project_id,
                req.objective_id,
                req.capability_id,
                req.approval_mode,
                req.risk_level,
                Json(req.inputs),
                req.requested_by,
            ),
        )
        row = cur.fetchone()
        conn.commit()
        return {"ok": True, "job": row}


@router.post("/runner/claim", dependencies=[Depends(require_runner_secret)])
def claim_job(req: ClaimJobRequest):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            '''
            select id, project_id, objective_id, capability_id, approval_mode,
                   risk_level, inputs, requested_by, created_at
            from jobs
            where status = 'queued'
            order by created_at asc
            limit 1
            '''
        )
        job = cur.fetchone()

        if not job:
            return {"ok": True, "job": None}

        cur.execute(
            '''
            update jobs
            set status = 'running',
                started_at = now(),
                updated_at = now()
            where id = %s
            ''',
            (job["id"],),
        )
        conn.commit()
        return {"ok": True, "job": job}


@router.post("/runner/complete", dependencies=[Depends(require_runner_secret)])
def complete_job(req: CompleteJobRequest):
    final_status = req.status if req.status in ("completed", "failed") else "failed"

    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            '''
            update jobs
            set status = %s,
                result = %s,
                error = %s,
                completed_at = now(),
                updated_at = now()
            where id = %s
            returning id, status, result, error, completed_at
            ''',
            (
                final_status,
                Json(req.result) if req.result is not None else None,
                req.error,
                req.job_id,
            ),
        )
        row = cur.fetchone()
        conn.commit()
        return {"ok": True, "job": row}
