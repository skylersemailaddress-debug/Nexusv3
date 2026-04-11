from __future__ import annotations

import json
from datetime import date, datetime
from typing import Any

from fastapi import HTTPException
from psycopg import errors
from psycopg.types.json import Json

from app.db import get_conn
from app.settings import settings
from app.services.audit_log import create_audit_event
from app.services.observability import bind_context, get_request_context, metrics_registry

SYSTEM_MODES = {"active", "paused", "degraded"}
RUNNER_STATES = {"active", "paused", "draining"}


def _json_default(value: Any):
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def get_system_mode(cur=None) -> dict[str, Any]:
    owns_conn = cur is None
    conn = get_conn() if owns_conn else None
    cursor = cur or conn.cursor()
    try:
        try:
            cursor.execute(
                """
                insert into system_control_plane (system_key, mode, reason, updated_by)
                values ('global', 'active', 'bootstrap', 'system')
                on conflict (system_key) do nothing
                """
            )
            cursor.execute(
                """
                select system_key, mode, reason, updated_by, updated_at
                from system_control_plane
                where system_key = 'global'
                """
            )
            row = cursor.fetchone()
        except errors.UndefinedTable:
            row = {"system_key": "global", "mode": "active", "reason": "compatibility-fallback", "updated_by": "system", "updated_at": None}
        if owns_conn:
            conn.commit()
        return row
    finally:
        if owns_conn:
            close_cursor = getattr(cursor, "close", None)
            if callable(close_cursor):
                close_cursor()
            close_conn = getattr(conn, "close", None)
            if callable(close_conn):
                close_conn()


def set_system_mode(mode: str, actor: str, role: str, reason: str | None = None) -> dict[str, Any]:
    normalized = mode.strip().lower()
    if normalized not in SYSTEM_MODES:
        raise HTTPException(status_code=400, detail="Invalid system mode")
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            insert into system_control_plane (system_key, mode, reason, updated_by)
            values ('global', %s, %s, %s)
            on conflict (system_key) do update
            set mode = excluded.mode,
                reason = excluded.reason,
                updated_by = excluded.updated_by,
                updated_at = now()
            returning system_key, mode, reason, updated_by, updated_at
            """,
            (normalized, reason, actor),
        )
        row = cur.fetchone()
        create_audit_event(
            "control_plane.mode_changed",
            actor,
            role,
            outcome="success",
            details={"mode": normalized, "reason": reason},
            cur=cur,
        )
        conn.commit()
        return row


def ensure_system_allows_execution(action: str) -> dict[str, Any]:
    state = get_system_mode()
    mode = state.get("mode") or "active"
    if mode == "paused":
        raise HTTPException(status_code=423, detail=f"System is paused; action blocked: {action}")
    return state


def record_runner_heartbeat(
    runner_id: str,
    *,
    status: str,
    project_id: str | None = None,
    job_id: str | None = None,
    capabilities: list[str] | None = None,
    max_concurrency: int | None = None,
    meta: dict[str, Any] | None = None,
    cur=None,
) -> dict[str, Any]:
    bind_context(project_id=project_id, job_id=job_id)
    owns_conn = cur is None
    conn = get_conn() if owns_conn else None
    cursor = cur or conn.cursor()
    try:
        cursor.execute(
            """
            insert into runner_heartbeats (
                runner_id,
                status,
                project_id,
                job_id,
                last_heartbeat,
                meta,
                capabilities,
                max_concurrency
            )
            values (%s, %s, %s, %s, now(), %s, %s, %s)
            on conflict (runner_id) do update
            set status = excluded.status,
                project_id = excluded.project_id,
                job_id = excluded.job_id,
                last_heartbeat = excluded.last_heartbeat,
                meta = runner_heartbeats.meta || excluded.meta,
                capabilities = case
                    when jsonb_array_length(excluded.capabilities) > 0 then excluded.capabilities
                    else runner_heartbeats.capabilities
                end,
                max_concurrency = greatest(1, coalesce(excluded.max_concurrency, runner_heartbeats.max_concurrency))
            returning runner_id, status, project_id, job_id, last_heartbeat, meta, capabilities, max_concurrency, desired_state, last_claim_at
            """,
            (
                runner_id,
                status,
                project_id,
                job_id,
                Json(meta or {}),
                Json(capabilities or []),
                max(1, int(max_concurrency or 1)),
            ),
        )
        row = cursor.fetchone()
        if owns_conn:
            conn.commit()
        return row
    finally:
        if owns_conn:
            close_cursor = getattr(cursor, "close", None)
            if callable(close_cursor):
                close_cursor()
            close_conn = getattr(conn, "close", None)
            if callable(close_conn):
                close_conn()


def list_runners() -> list[dict[str, Any]]:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            select
              rh.runner_id,
              rh.status,
              rh.project_id,
              rh.job_id,
              rh.last_heartbeat,
              rh.meta,
              rh.capabilities,
              rh.max_concurrency,
              rh.desired_state,
              rh.last_claim_at,
              count(j.*) filter (
                where j.status = 'running'
                  and (j.lease_expires_at is null or j.lease_expires_at > now())
              ) as active_jobs
            from runner_heartbeats rh
            left join jobs j
              on j.claimed_by = rh.runner_id
            group by
              rh.runner_id, rh.status, rh.project_id, rh.job_id, rh.last_heartbeat, rh.meta,
              rh.capabilities, rh.max_concurrency, rh.desired_state, rh.last_claim_at
            order by rh.last_heartbeat desc, rh.runner_id asc
            """
        )
        return cur.fetchall()


def list_jobs(status: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
    clauses = []
    params: list[Any] = []
    if status:
        clauses.append("status = %s")
        params.append(status)
    where = f"where {' and '.join(clauses)}" if clauses else ""
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            f"""
            select id, project_id, capability_id, status, claimed_by, approval_required, approval_status,
                   created_at, updated_at, started_at, completed_at, inputs, error,
                   retry_count, max_retries, next_retry_at, lease_expires_at, dead_lettered_at,
                   failure_class, failure_signature, retry_policy, last_failure_at
            from jobs
            {where}
            order by updated_at desc nulls last, created_at desc
            limit %s
            """,
            (*params, limit),
        )
        return cur.fetchall()


def list_project_health() -> list[dict[str, Any]]:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            select
              p.id,
              p.name,
              p.status,
              ps.current_objective,
              ps.next_step,
              ps.version_no,
              ps.updated_at,
              count(j.*) filter (where j.status in ('queued', 'running', 'awaiting_approval')) as active_jobs,
              count(j.*) filter (where j.status in ('failed', 'dead_letter')) as failed_jobs,
              max(j.updated_at) as last_job_update
            from projects p
            left join project_state ps on ps.project_id = p.id
            left join jobs j on j.project_id = p.id
            group by p.id, p.name, p.status, ps.current_objective, ps.next_step, ps.version_no, ps.updated_at
            order by p.updated_at desc, p.id asc
            """
        )
        rows = cur.fetchall()
    items = []
    for row in rows:
        health = "healthy"
        if (row.get("failed_jobs") or 0) > 0:
            health = "warning"
        if (row.get("active_jobs") or 0) > 5:
            health = "busy"
        items.append({**row, "health": health})
    return items


def fetch_db_metrics() -> dict[str, float | int | None]:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            select
              count(*) as jobs_total,
              count(*) filter (where status in ('failed', 'dead_letter')) as jobs_failed_total,
              count(*) filter (where status = 'dead_letter') as jobs_dead_letter_total,
              count(*) filter (where coalesce((inputs->>'attempt_count')::int, 0) > 0) as jobs_retried_total,
              count(*) filter (where status in ('queued', 'retrying', 'running')) as queue_depth,
              count(*) filter (where status = 'retrying') as retry_scheduled_jobs,
              count(*) filter (where approval_status = 'pending' or status = 'awaiting_approval') as approval_pending_jobs,
              count(*) filter (where status = 'running' and lease_expires_at is not null and lease_expires_at < now()) as stale_leases,
              avg(extract(epoch from (completed_at - started_at))) filter (
                where completed_at is not null and started_at is not null
              ) as job_latency_average_seconds
            from jobs
            """
        )
        row = cur.fetchone() or {}
        cur.execute(
            """
            select
              count(*) filter (where last_heartbeat < now() - (%s * interval '1 second')) as stale_runners,
              count(*) filter (where desired_state = 'paused') as paused_runners,
              count(*) filter (where desired_state = 'draining') as draining_runners,
              coalesce(sum(greatest(max_concurrency, 1)), 0) as runner_capacity
            from runner_heartbeats
            """,
            (settings.runner_stale_after_seconds,),
        )
        runner_row = cur.fetchone() or {}
    queue_depth = int(row.get("queue_depth") or 0)
    runner_capacity = int(runner_row.get("runner_capacity") or 0)
    stale_leases = int(row.get("stale_leases") or 0)
    stale_runners = int(runner_row.get("stale_runners") or 0)
    row["stale_runners"] = stale_runners
    row["paused_runners"] = int(runner_row.get("paused_runners") or 0)
    row["draining_runners"] = int(runner_row.get("draining_runners") or 0)
    row["runner_capacity"] = runner_capacity
    if stale_leases > 0 or stale_runners > 0 or (runner_capacity > 0 and queue_depth > runner_capacity * 3):
        row["queue_pressure"] = "critical"
    elif queue_depth > max(runner_capacity, 1):
        row["queue_pressure"] = "elevated"
    else:
        row["queue_pressure"] = "nominal"
    metrics_registry.set_gauge("queue_depth_observed", float(row.get("queue_depth") or 0))
    metrics_registry.set_gauge("approval_pending_observed", float(row.get("approval_pending_jobs") or 0))
    metrics_registry.set_gauge("stale_leases_observed", float(stale_leases))
    metrics_registry.set_gauge("stale_runners_observed", float(stale_runners))
    return row


def lease_duration_sql() -> str:
    return f"interval '{int(settings.job_lease_seconds)} seconds'"


def runner_stale_seconds() -> int:
    return int(settings.runner_stale_after_seconds)


def compute_retry_backoff_seconds(next_retry_count: int) -> int:
    multiplier = max(0, next_retry_count - 1)
    seconds = int(settings.retry_backoff_base_seconds) * (2**multiplier)
    return min(seconds, int(settings.retry_backoff_max_seconds))


def release_expired_job_leases(cur) -> list[dict[str, Any]]:
    cur.execute(
        """
        update jobs
        set status = case
                when status = 'running' then 'queued'
                else status
            end,
            claimed_by = null,
            claim_token = null,
            lease_expires_at = null,
            started_at = null,
            updated_at = now(),
            error = trim(
                both ' '
                from concat_ws(' | ', nullif(error, ''), 'Recovered expired lease for reassignment')
            )
        where status = 'running'
          and lease_expires_at is not null
          and lease_expires_at < now()
        returning id, project_id, capability_id, status
        """
    )
    return cur.fetchall()


def renew_runner_leases(runner_id: str, job_ids: list[str], *, cur=None) -> list[dict[str, Any]]:
    if not job_ids:
        return []
    owns_conn = cur is None
    conn = get_conn() if owns_conn else None
    cursor = cur or conn.cursor()
    try:
        cursor.execute(
            f"""
            update jobs
            set lease_expires_at = now() + {lease_duration_sql()},
                updated_at = now()
            where claimed_by = %s
              and status = 'running'
              and id = any(%s)
            returning id, lease_expires_at
            """,
            (runner_id, job_ids),
        )
        rows = cursor.fetchall()
        if owns_conn:
            conn.commit()
        return rows
    finally:
        if owns_conn:
            close_cursor = getattr(cursor, "close", None)
            if callable(close_cursor):
                close_cursor()
            close_conn = getattr(conn, "close", None)
            if callable(close_conn):
                close_conn()


def set_runner_desired_state(runner_id: str, desired_state: str, actor: str, role: str) -> dict[str, Any]:
    normalized = desired_state.strip().lower()
    if normalized not in RUNNER_STATES:
        raise HTTPException(status_code=400, detail="Invalid runner state")
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            insert into runner_heartbeats (
                runner_id,
                status,
                last_heartbeat,
                meta,
                capabilities,
                max_concurrency,
                desired_state
            )
            values (%s, 'idle', now(), '{}'::jsonb, '[]'::jsonb, 1, %s)
            on conflict (runner_id) do update
            set desired_state = excluded.desired_state,
                last_heartbeat = runner_heartbeats.last_heartbeat
            returning runner_id, status, project_id, job_id, last_heartbeat, meta, capabilities, max_concurrency, desired_state, last_claim_at
            """,
            (runner_id, normalized),
        )
        row = cur.fetchone()
        create_audit_event(
            "admin.runner.state",
            actor,
            role,
            outcome="success",
            details={"runner_id": runner_id, "desired_state": normalized},
            cur=cur,
        )
        conn.commit()
        return row


def snapshot_project_state(
    project_id: str,
    state_row: dict[str, Any] | None,
    *,
    source: str,
    job_id: str | None = None,
    artifact_id: str | None = None,
    cur=None,
) -> dict[str, Any] | None:
    if not project_id or not state_row:
        return None
    request_id = get_request_context().get("request_id")
    owns_conn = cur is None
    conn = get_conn() if owns_conn else None
    cursor = cur or conn.cursor()
    try:
        cursor.execute(
            """
            insert into state_versions (project_id, version_no, source, request_id, job_id, artifact_id, snapshot)
            values (%s, %s, %s, %s, %s, %s, %s)
            returning id, project_id, version_no, source, request_id, job_id, artifact_id, snapshot, created_at
            """,
            (
                project_id,
                state_row.get("version_no") or 0,
                source,
                request_id,
                job_id,
                artifact_id,
                Json(state_row, dumps=lambda obj: json.dumps(obj, default=_json_default)),
            ),
        )
        fetchone = getattr(cursor, "fetchone", None)
        row = fetchone() if callable(fetchone) else None
        if owns_conn:
            conn.commit()
        return row or {
            "project_id": project_id,
            "version_no": state_row.get("version_no") or 0,
            "source": source,
            "request_id": request_id,
            "job_id": job_id,
            "artifact_id": artifact_id,
            "snapshot": state_row,
        }
    finally:
        if owns_conn:
            close_cursor = getattr(cursor, "close", None)
            if callable(close_cursor):
                close_cursor()
            close_conn = getattr(conn, "close", None)
            if callable(close_conn):
                close_conn()
