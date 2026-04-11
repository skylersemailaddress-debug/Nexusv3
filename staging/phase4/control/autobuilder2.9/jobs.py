from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from psycopg.types.json import Json

from app.auth import require_api_token
from app.db import get_conn
from app.services.audit_log import create_audit_event
from app.services.autocode import maybe_start_autocode
from app.services.autocode_policy import is_autocode_eligible
from app.services.control_plane import (
    compute_retry_backoff_seconds,
    ensure_system_allows_execution,
    lease_duration_sql,
    record_runner_heartbeat,
    release_expired_job_leases,
    snapshot_project_state,
)
from app.services.execution_writeback import enforce_writeback
from app.services.automation_triggers import dispatch_event_trigger
from app.services.failure_intelligence import classify_failure, persist_failure_state
from app.services.observability import bind_context, record_job_event
from app.services.plan_execution import handle_step_completion
from app.services.project_os import refresh_project_direction
from app.services.retry_policy import plan_retry

router = APIRouter(prefix="/jobs", tags=["jobs"])


def _latency_seconds(started_at, completed_at) -> float | None:
    if not started_at or not completed_at:
        return None
    if isinstance(started_at, str) or isinstance(completed_at, str):
        return None
    if isinstance(started_at, datetime) and isinstance(completed_at, datetime):
        return (completed_at - started_at).total_seconds()
    return None


class ClaimJobRequest(BaseModel):
    runner_id: str
    project_id: str | None = None
    capabilities: list[str] | None = None
    max_concurrency: int | None = None


class CompleteJobRequest(BaseModel):
    job_id: str
    runner_id: str
    status: str
    result: dict[str, Any] | None = None
    error: str | None = None


class ApprovalDecisionRequest(BaseModel):
    actor: str
    decision: str
    reason: str | None = None


def _ensure_project_exists(cur, project_id: str) -> None:
    cur.execute(
        """
        insert into projects (id, name, status)
        values (%s, %s, 'active')
        on conflict (id) do nothing
        """,
        (project_id, project_id),
    )


def _get_job(cur, job_id: str):
    cur.execute("select * from jobs where id = %s", (job_id,))
    return cur.fetchone()


def _get_job_result_artifact(cur, job_id: str):
    cur.execute(
        "select * from artifacts "
        "where kind = 'job_result' "
        "and (meta->>'job_id' = %s or payload->>'job_id' = %s) "
        "order by created_at desc limit 1",
        (job_id, job_id),
    )
    return cur.fetchone()


def _get_project_state(cur, project_id: str):
    cur.execute("select * from project_state where project_id = %s", (project_id,))
    return cur.fetchone()


def _write_job_event(cur, project_id: str | None, event_name: str, job_id: str, payload: dict[str, Any] | None = None):
    if not project_id:
        return None
    cur.execute(
        """
        insert into events (project_id, event_name, object_type, object_id, payload)
        values (%s, %s, 'job', %s, %s)
        """,
        (project_id, event_name, job_id, Json(payload or {})),
    )


def _create_job_artifact(cur, updated_job: dict, status: str, result: dict[str, Any], error_text: str):
    job_id = updated_job["id"]
    artifact_payload = {
        "job_id": job_id,
        "capability_id": updated_job["capability_id"],
        "status": status,
        "result": result,
        "error": error_text,
    }
    cur.execute(
        """
        insert into artifacts (id, project_id, kind, title, path, payload, meta)
        values (%s, %s, 'job_result', %s, %s, %s, %s)
        returning *
        """,
        (
            f"artifact-job-{job_id}",
            updated_job["project_id"],
            f"Job result: {job_id}",
            None,
            Json(artifact_payload),
            Json({"source": "runner.complete", "job_id": job_id}),
        ),
    )
    return cur.fetchone()


def _upsert_project_state_success(cur, project_id: str, job_id: str, capability_id: str, result: dict):
    cur.execute(
        """
        insert into project_state (
            id,
            project_id,
            current_objective,
            next_step,
            status,
            structured_state,
            version_no,
            updated_at
        )
        values (
            %s,
            %s,
            null,
            null,
            'active',
            %s,
            1,
            now()
        )
        on conflict (project_id) do update
        set structured_state = jsonb_set(
                coalesce(project_state.structured_state, '{}'::jsonb),
                '{meta}',
                coalesce(project_state.structured_state->'meta', '{}'::jsonb) || coalesce(excluded.structured_state->'meta', '{}'::jsonb),
                true
            ),
            version_no = project_state.version_no + 1,
            updated_at = now()
        returning *
        """,
        (
            f"state-{project_id}",
            project_id,
            Json(
                {
                    "meta": {
                        "last_completed_job_id": job_id,
                        "last_completed_capability_id": capability_id,
                        "last_job_result": result,
                        "last_job_artifact_id": f"artifact-job-{job_id}",
                    }
                }
            ),
        ),
    )
    return cur.fetchone()


def _apply_state_writeback(cur, updated_job: dict, status: str, result: dict[str, Any]):
    return _upsert_project_state_success(
        cur,
        updated_job["project_id"],
        updated_job["id"],
        updated_job["capability_id"],
        result,
    )


def _attempt_count_from_job(job: dict[str, Any]) -> int:
    return int((job.get("inputs") or {}).get("attempt_count") or 0)


def _with_attempt_count(inputs: dict[str, Any] | None, attempt_count: int) -> dict[str, Any]:
    next_inputs = dict(inputs or {})
    next_inputs["attempt_count"] = attempt_count
    return next_inputs


@router.post("/enqueue", dependencies=[Depends(require_api_token)])
def enqueue_job(payload: dict):
    project_id = payload.get("project_id")
    job_id = payload.get("id")
    capability_id = payload.get("capability_id")

    if not project_id or not job_id or not capability_id:
        raise HTTPException(status_code=400, detail="Missing required fields")

    ensure_system_allows_execution("jobs.enqueue")
    bind_context(project_id=project_id, job_id=job_id)
    with get_conn() as conn, conn.cursor() as cur:
        _ensure_project_exists(cur, project_id)
        approval_required = bool(payload.get("approval_required")) or (payload.get("approval_mode") in {"manual", "approval_required"})
        initial_status = "awaiting_approval" if approval_required else "queued"
        approval_status = "pending" if approval_required else "not_required"
        cur.execute(
            """
            insert into jobs (
                id, project_id, objective_id, capability_id,
                status, approval_mode, risk_level, inputs,
                requested_by, approval_required, approval_status, started_at, completed_at,
                created_at, updated_at, claimed_by, claim_token,
                retry_count, max_retries, next_retry_at, lease_expires_at, dead_lettered_at
            )
            values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, null, null, now(), now(), null, null, %s, %s, null, null, null)
            returning *
            """,
            (
                job_id,
                project_id,
                payload.get("objective_id"),
                capability_id,
                initial_status,
                payload.get("approval_mode") or "auto_read",
                payload.get("risk_level") or "low",
                Json(payload.get("inputs") or {}),
                payload.get("requested_by"),
                approval_required,
                approval_status,
                int(payload.get("retry_count") or 0),
                max(0, int(payload.get("max_retries") or 0)),
            ),
        )
        job = cur.fetchone()
        _write_job_event(cur, project_id, "job.enqueued", job_id, {"capability_id": capability_id, "approval_required": approval_required})
        create_audit_event(
            "job.enqueued",
            payload.get("requested_by") or "system",
            "user",
            project_id=project_id,
            job_id=job_id,
            details={"capability_id": capability_id, "approval_required": approval_required},
            cur=cur,
        )
        conn.commit()
    if approval_required:
        dispatch_event_trigger("approval_pending", project_id=project_id, payload={"job_id": job_id})
    return {"ok": True, "job": job}


def claim_job_logic(body: dict):
    project_id = body.get("project_id")
    runner_id = body.get("runner_id")
    capabilities = [item for item in (body.get("capabilities") or []) if item]
    max_concurrency = max(1, int(body.get("max_concurrency") or 1))
    if not runner_id:
        raise HTTPException(status_code=400, detail="Missing runner_id")

    ensure_system_allows_execution("jobs.claim")
    bind_context(project_id=project_id)
    with get_conn() as conn, conn.cursor() as cur:
        runner = record_runner_heartbeat(
            runner_id,
            status="idle",
            project_id=project_id,
            capabilities=capabilities,
            max_concurrency=max_concurrency,
            meta={"source": "jobs.claim"},
            cur=cur,
        )
        recovered_stale_jobs = len(release_expired_job_leases(cur))
        if (runner.get("desired_state") or "active") != "active":
            conn.commit()
            return {"ok": True, "job": None, "recovered_stale_jobs": recovered_stale_jobs, "runner_state": runner.get("desired_state")}

        cur.execute(
            """
            select count(*) as active_jobs
            from jobs
            where claimed_by = %s
              and status = 'running'
              and (lease_expires_at is null or lease_expires_at > now())
            """,
            (runner_id,),
        )
        active_jobs = int((cur.fetchone() or {}).get("active_jobs") or 0)
        if active_jobs >= max_concurrency:
            conn.commit()
            return {"ok": True, "job": None, "recovered_stale_jobs": recovered_stale_jobs, "runner_state": runner.get("desired_state")}

        where_clauses = [
            "status in ('queued', 'retrying')",
            "(next_retry_at is null or next_retry_at <= now())",
        ]
        params: list[Any] = []
        if project_id:
            where_clauses.append("project_id = %s")
            params.append(project_id)
        if capabilities:
            where_clauses.append("capability_id = any(%s)")
            params.append(capabilities)

        cur.execute(
            f"""
            select id
            from jobs
            where {' and '.join(where_clauses)}
            order by
              case when status = 'retrying' then 0 else 1 end asc,
              coalesce(next_retry_at, created_at) asc,
              created_at asc
            for update skip locked
            limit 1
            """,
            tuple(params),
        )
        row = cur.fetchone()
        if not row:
            conn.commit()
            return {"ok": True, "job": None, "recovered_stale_jobs": recovered_stale_jobs}

        job_id = row["id"]
        claim_token = uuid4().hex
        cur.execute(
            f"""
            update jobs
            set status = 'running',
                claimed_by = %s,
                claim_token = %s,
                started_at = now(),
                completed_at = null,
                updated_at = now(),
                next_retry_at = null,
                lease_expires_at = now() + {lease_duration_sql()}
            where id = %s
            returning *
            """,
            (runner_id, claim_token, job_id),
        )
        job = cur.fetchone() or {**row, "claimed_by": runner_id, "claim_token": claim_token}
        bind_context(project_id=job.get("project_id"), job_id=job_id)
        _write_job_event(cur, job.get("project_id"), "job.claimed", job_id, {"runner_id": runner_id})
        record_runner_heartbeat(
            runner_id,
            status="running",
            project_id=job.get("project_id"),
            job_id=job_id,
            capabilities=capabilities,
            max_concurrency=max_concurrency,
            meta={"source": "jobs.claim"},
            cur=cur,
        )
        cur.execute(
            """
            update runner_heartbeats
            set last_claim_at = now()
            where runner_id = %s
            """,
            (runner_id,),
        )
        conn.commit()
        return {"ok": True, "job": job, "recovered_stale_jobs": recovered_stale_jobs}


def complete_job_logic(body: dict):
    job_id = body.get("job_id")
    runner_id = body.get("runner_id")
    status = body.get("status")
    result = body.get("result") or {}
    error_text = body.get("error") or ""

    if not job_id or not runner_id or status not in {"completed", "failed"}:
        raise HTTPException(status_code=400, detail="Missing or invalid completion fields")

    ensure_system_allows_execution("jobs.complete")
    bind_context(job_id=job_id)
    with get_conn() as conn, conn.cursor() as cur:
        job = _get_job(cur, job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
        bind_context(project_id=job.get("project_id"), job_id=job_id)

        # Idempotent replay
        if job["status"] in {"completed", "failed", "dead_letter"}:
            artifact = _get_job_result_artifact(cur, job_id)
            project_state = _get_project_state(cur, job.get("project_id")) if job["status"] == "completed" else None
            return {
                "ok": True,
                "job": job,
                "artifact": artifact,
                "project_state": project_state,
                "idempotent": True,
            }

        if job["status"] != "running":
            raise HTTPException(status_code=409, detail=f"Job is not running: {job_id}")
        if job.get("claimed_by") != runner_id:
            raise HTTPException(status_code=409, detail="Job is owned by a different runner")
        if job.get("lease_expires_at") and isinstance(job["lease_expires_at"], datetime) and job["lease_expires_at"] < datetime.now(job["lease_expires_at"].tzinfo):
            raise HTTPException(status_code=409, detail="Job lease has expired")

        terminal_status = status
        event_name = "job.completed"
        audit_action = "job.completed"
        attempt_count = _attempt_count_from_job(job)
        record_status = status
        if status == "completed":
            cur.execute(
                """
                update jobs
                set status = 'completed',
                    result = %s,
                    error = %s,
                    failure_class = null,
                    failure_signature = null,
                    completed_at = now(),
                    updated_at = now(),
                    claimed_by = null,
                    claim_token = null,
                    lease_expires_at = null,
                    next_retry_at = null
                where id = %s
                returning *
                """,
                (Json(result), error_text, job_id),
            )
        else:
            classification = classify_failure(job, result, error_text)
            retry_plan = plan_retry(job, classification)
            next_retry_count = retry_plan["next_retry_count"]
            inputs = _with_attempt_count(job.get("inputs"), next_retry_count)
            if retry_plan["should_retry"]:
                terminal_status = "retrying"
                event_name = "job.retry_scheduled"
                audit_action = "job.retry_scheduled"
                record_status = "retrying"
                cur.execute(
                    """
                    update jobs
                    set status = 'retrying',
                        result = %s,
                        error = %s,
                        completed_at = now(),
                        updated_at = now(),
                        claimed_by = null,
                        claim_token = null,
                        lease_expires_at = null,
                        retry_count = %s,
                        max_retries = %s,
                        last_retry_at = now(),
                        next_retry_at = now() + (%s * interval '1 second'),
                        inputs = %s,
                        failure_class = %s,
                        failure_signature = %s,
                        retry_policy = %s,
                        last_failure_at = now()
                    where id = %s
                    returning *
                    """,
                    (
                        Json(result),
                        error_text,
                        next_retry_count,
                        retry_plan["max_retries"],
                        retry_plan["backoff_seconds"],
                        Json(inputs),
                        classification["failure_class"],
                        classification["failure_signature"],
                        retry_plan["policy"].name,
                        job_id,
                    ),
                )
            else:
                terminal_status = "dead_letter"
                event_name = "job.dead_lettered"
                audit_action = "job.dead_lettered"
                record_status = "dead_letter"
                cur.execute(
                    """
                    update jobs
                    set status = 'dead_letter',
                        result = %s,
                        error = %s,
                        completed_at = now(),
                        updated_at = now(),
                        claimed_by = null,
                        claim_token = null,
                        lease_expires_at = null,
                        retry_count = %s,
                        max_retries = %s,
                        dead_lettered_at = now(),
                        inputs = %s,
                        failure_class = %s,
                        failure_signature = %s,
                        retry_policy = %s,
                        last_failure_at = now()
                    where id = %s
                    returning *
                    """,
                    (
                        Json(result),
                        error_text,
                        next_retry_count,
                        retry_plan["max_retries"],
                        Json(inputs),
                        classification["failure_class"],
                        classification["failure_signature"],
                        retry_plan["policy"].name,
                        job_id,
                    ),
                )
        updated_job = cur.fetchone()
        if status == "failed":
            persist_failure_state(
                cur,
                job_id=updated_job["id"],
                classification=classification,
                retry_policy_name=retry_plan["policy"].name,
                extra_meta={"failure": classification},
            )
        artifact = _create_job_artifact(cur, updated_job, terminal_status, result, error_text)
        enforce_writeback(cur, updated_job["project_id"], updated_job["id"], result)
        project_state = _apply_state_writeback(cur, updated_job, terminal_status, result) if terminal_status == "completed" else None
        if project_state:
            snapshot_project_state(
                updated_job["project_id"],
                project_state,
                source=f"jobs.{terminal_status}",
                job_id=updated_job["id"],
                artifact_id=artifact["id"] if artifact else None,
                cur=cur,
            )
        direction = refresh_project_direction(
            cur,
            updated_job["project_id"],
            trigger="job.complete",
            latest_job_id=updated_job["id"],
            latest_artifact_id=artifact["id"] if artifact else None,
        )
        autocode = None
        if terminal_status == "dead_letter":
            policy = is_autocode_eligible(updated_job, classification)
            autocode = maybe_start_autocode(cur, updated_job, result, error_text, classification, policy)
            dispatch_event_trigger(
                "dead_letter_created",
                project_id=updated_job.get("project_id"),
                payload={"job_id": updated_job["id"], "failure_class": classification.get("failure_class")},
            )

        plan_state = handle_step_completion(cur, updated_job, terminal_status, result, error_text)
        if plan_state and plan_state.get("status") == "blocked":
            dispatch_event_trigger(
                "plan_blocked",
                project_id=updated_job.get("project_id"),
                payload={"job_id": updated_job["id"], "plan_id": (updated_job.get("inputs") or {}).get("plan_id")},
            )

        _write_job_event(
            cur,
            updated_job.get("project_id"),
            event_name,
            job_id,
            {"status": terminal_status, "runner_id": runner_id},
        )
        create_audit_event(
            audit_action,
            runner_id,
            "operator",
            project_id=updated_job.get("project_id"),
            job_id=job_id,
            details={"status": terminal_status},
            cur=cur,
        )
        record_runner_heartbeat(
            runner_id,
            status="idle" if terminal_status in {"completed", "retrying"} else "error",
            project_id=updated_job.get("project_id"),
            job_id=job_id,
            meta={"source": "jobs.complete", "status": terminal_status},
            cur=cur,
        )
        started_at = updated_job.get("started_at")
        completed_at = updated_job.get("completed_at")
        latency_seconds = _latency_seconds(started_at, completed_at)
        record_job_event(record_status, attempts=int((updated_job.get("inputs") or {}).get("attempt_count") or attempt_count), latency_seconds=latency_seconds)

        conn.commit()
        return {
            "ok": True,
            "job": updated_job,
            "artifact": artifact,
            "project_state": project_state or direction["project_state"],
            "plan_state": plan_state,
            "autocode": autocode,
            "idempotent": False,
        }


@router.post("/claim", dependencies=[Depends(require_api_token)])
def claim_job(body: ClaimJobRequest):
    return claim_job_logic(body.model_dump())


@router.post("/complete", dependencies=[Depends(require_api_token)])
def complete_job(body: CompleteJobRequest):
    return complete_job_logic(body.model_dump())


@router.post("/{job_id}/approval", dependencies=[Depends(require_api_token)])
def decide_job_approval(job_id: str, body: ApprovalDecisionRequest):
    decision = body.decision.strip().lower()
    if decision not in {"approve", "reject"}:
        raise HTTPException(status_code=400, detail="Decision must be approve or reject")

    with get_conn() as conn, conn.cursor() as cur:
        job = _get_job(cur, job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
        bind_context(project_id=job.get("project_id"), job_id=job_id)
        if job.get("status") != "awaiting_approval":
            raise HTTPException(status_code=409, detail="Job is not awaiting approval")

        if decision == "approve":
            cur.execute(
                """
                update jobs
                set status = 'queued',
                    approval_status = 'approved',
                    approved_by = %s,
                    approved_at = now(),
                    updated_at = now(),
                    next_retry_at = null,
                    dead_lettered_at = null
                where id = %s
                returning *
                """,
                (body.actor, job_id),
            )
            updated = cur.fetchone()
            _write_job_event(cur, updated.get("project_id"), "job.approved", job_id, {"actor": body.actor})
            create_audit_event("job.approved", body.actor, "operator", project_id=updated.get("project_id"), job_id=job_id, cur=cur)
        else:
            cur.execute(
                """
                update jobs
                set status = 'dead_letter',
                    approval_status = 'rejected',
                    rejected_by = %s,
                    rejected_at = now(),
                    rejection_reason = %s,
                    error = coalesce(%s, 'Rejected by reviewer'),
                    completed_at = now(),
                    updated_at = now(),
                    dead_lettered_at = now()
                where id = %s
                returning *
                """,
                (body.actor, body.reason, body.reason, job_id),
            )
            updated = cur.fetchone()
            _write_job_event(cur, updated.get("project_id"), "job.rejected", job_id, {"actor": body.actor, "reason": body.reason})
            create_audit_event(
                "job.rejected",
                body.actor,
                "operator",
                project_id=updated.get("project_id"),
                job_id=job_id,
                details={"reason": body.reason},
                cur=cur,
            )

        conn.commit()
        return {"ok": True, "job": updated}
