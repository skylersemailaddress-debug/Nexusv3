from __future__ import annotations

from typing import Any
from uuid import uuid4

from psycopg.types.json import Json

from app.db import get_conn
from app.services.connectors import write_artifact_via_connector
from app.services.control_plane import ensure_system_allows_execution, snapshot_project_state
from app.services.observability import bind_context, record_loop_iteration
from app.services.project_os import refresh_project_direction, set_ramble_mode
from app.services.ramble import capture_ramble


def _enqueue_execution_job(cur, project_id: str, objective_id: str | None, requested_by: str, title: str, approval_required: bool = False) -> dict[str, Any]:
    job_id = f"job_{uuid4().hex}"
    status = "awaiting_approval" if approval_required else "queued"
    approval_status = "pending" if approval_required else "not_required"
    command = "Write-Output '{}'".format(title.replace("'", "''"))
    cur.execute(
        """
        insert into jobs (
            id, project_id, objective_id, capability_id, status, approval_mode, risk_level, inputs,
            requested_by, approval_required, approval_status, started_at, completed_at, created_at, updated_at
        )
        values (%s, %s, %s, 'local.powershell', %s, %s, 'low', %s, %s, %s, %s, null, null, now(), now())
        returning *
        """,
        (
            job_id,
            project_id,
            objective_id,
            status,
            "manual" if approval_required else "auto_read",
            Json({"command": command, "attempt_count": 0, "source": "automation_loop"}),
            requested_by,
            approval_required,
            approval_status,
        ),
    )
    return cur.fetchone()


def _latest_execution_payload(cur, project_id: str) -> dict[str, Any] | None:
    cur.execute(
        """
        select id, kind, title, payload, meta
        from artifacts
        where project_id = %s
          and kind in ('execution_result', 'job_result')
        order by created_at desc
        limit 1
        """,
        (project_id,),
    )
    return cur.fetchone()


def _active_job_count(cur, project_id: str) -> int:
    cur.execute(
        """
        select count(*) as count
        from jobs
        where project_id = %s
          and status in ('queued', 'running', 'awaiting_approval')
        """,
        (project_id,),
    )
    row = cur.fetchone() or {}
    return int(row.get("count") or 0)


def run_automation_tick(project_id: str, requested_by: str = "automation-loop", max_actions: int = 3) -> dict[str, Any]:
    ensure_system_allows_execution("automation.tick")
    bind_context(project_id=project_id)
    record_loop_iteration()
    actions: list[dict[str, Any]] = []
    with get_conn() as conn, conn.cursor() as cur:
        for _ in range(max_actions):
            plan = refresh_project_direction(cur, project_id, trigger="automation.tick")
            snapshot_project_state(project_id, plan.get("project_state"), source="automation.tick", cur=cur)
            if plan["resolved"]:
                actions.append({"kind": "resolved", "title": plan["next_step_title"]})
                break

            if _active_job_count(cur, project_id) > 0:
                actions.append({"kind": "waiting", "reason": "Active job already present"})
                break

            if plan["next_action_kind"] == "connector_sync":
                latest_execution = _latest_execution_payload(cur, project_id)
                if not latest_execution:
                    actions.append({"kind": "waiting", "reason": "No execution artifact available yet"})
                    break
                connector_artifact = write_artifact_via_connector(
                    cur,
                    project_id,
                    "mock-google-drive",
                    f"Connector sync for {project_id}",
                    {
                        "source_artifact_id": latest_execution["id"],
                        "source_kind": latest_execution["kind"],
                        "payload": latest_execution.get("payload") or {},
                    },
                    meta={"source": "automation.tick", "source_artifact_id": latest_execution["id"]},
                )
                refresh_project_direction(cur, project_id, trigger="automation.tick.connector_sync", latest_artifact_id=connector_artifact["id"])
                actions.append({"kind": "connector_sync", "artifact_id": connector_artifact["id"]})
                continue

            if plan["next_action_kind"] == "ramble_capture":
                conn.commit()
                capture = capture_ramble(
                    project_id,
                    f"Automation ramble for {project_id}: objective={plan['objective_title']} next_step={plan['next_step_title']}",
                    {"source": "automation_loop"},
                )
                actions.append({"kind": "ramble_capture", "artifact_id": capture["capture"]["id"]})
                with get_conn() as conn2, conn2.cursor() as cur2:
                    refresh_project_direction(cur2, project_id, trigger="automation.tick.ramble", latest_artifact_id=capture["capture"]["id"])
                    conn2.commit()
                break

            if plan["next_action_kind"] == "execution":
                job = _enqueue_execution_job(cur, project_id, plan["objective_id"], requested_by, plan["next_step_title"])
                refresh_project_direction(cur, project_id, trigger="automation.tick.enqueue", latest_job_id=job["id"])
                actions.append({"kind": "execution_job", "job_id": job["id"], "status": job["status"]})
                break

            actions.append({"kind": "idle", "reason": "No actionable step available"})
            break

        conn.commit()

    return {"ok": True, "project_id": project_id, "actions": actions}


def update_ramble_mode(project_id: str, enabled: bool) -> dict[str, Any]:
    bind_context(project_id=project_id)
    with get_conn() as conn, conn.cursor() as cur:
        state = set_ramble_mode(cur, project_id, enabled)
        refresh_project_direction(cur, project_id, trigger="ramble-mode.toggle")
        snapshot_project_state(project_id, state, source="ramble-mode.toggle", cur=cur)
        conn.commit()
    return {"ok": True, "project_id": project_id, "ramble_mode": enabled, "project_state": state}
