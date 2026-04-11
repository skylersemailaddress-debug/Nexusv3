"""Canonical loop-state normalization and patch building for SkyOS.

M1-01 establishes the first explicit loop-state schema surface. The goal is not
full final-form orchestration yet; the goal is to remove mystery blobs and make
loop-state reads and writes predictable, versioned, and testable.
"""

from __future__ import annotations

from typing import Any

LOOP_STATE_SCHEMA_VERSION = 1

_ALLOWED_OBJECTIVE_STATUSES = {
    "pending",
    "ready",
    "running",
    "waiting",
    "blocked",
    "failed",
    "done",
    "cancelled",
}


def _normalize_objective(item: Any) -> dict[str, Any] | None:
    if not isinstance(item, dict):
        return None

    status = str(item.get("status") or "pending").lower()
    if status not in _ALLOWED_OBJECTIVE_STATUSES:
        status = "pending"

    normalized = {
        "id": item.get("id"),
        "title": item.get("title"),
        "status": status,
        "priority": item.get("priority"),
        "blocked_by": list(item.get("blocked_by") or []),
        "depends_on": list(item.get("depends_on") or []),
        "updated_at": item.get("updated_at"),
    }

    return {key: value for key, value in normalized.items() if value not in (None, [], {})}


def normalize_loop_state(state: dict | None) -> dict[str, Any]:
    if not isinstance(state, dict):
        state = {}

    objectives = [
        normalized
        for normalized in (_normalize_objective(item) for item in (state.get("objectives") or []))
        if normalized is not None
    ]
    fingerprints = [str(item) for item in (state.get("fingerprints") or []) if item is not None]
    pending_jobs = [dict(item) for item in (state.get("pending_jobs") or []) if isinstance(item, dict)]

    normalized = {
        "schema_version": int(state.get("schema_version") or LOOP_STATE_SCHEMA_VERSION),
        "objective": state.get("objective"),
        "objectives": objectives,
        "pending_jobs": pending_jobs,
        "fingerprints": fingerprints,
        "result": state.get("result"),
        "last_result": state.get("last_result") or state.get("result"),
        "last_action": state.get("last_action"),
        "last_mode": state.get("last_mode"),
        "last_job_type": state.get("last_job_type"),
        "last_result_status": state.get("last_result_status"),
        "iteration_count": int(state.get("iteration_count") or 0),
        "updated_at": state.get("updated_at"),
    }

    return normalized


def build_loop_state_patch(
    project_id: str,
    frame: dict,
    recommendation: dict,
    job: dict,
    result: dict,
    trace: dict,
    previous_structured_state: dict,
    created_at: str,
) -> dict[str, Any]:
    prev = normalize_loop_state((previous_structured_state or {}).get("loop_state"))
    iteration = int(prev.get("iteration_count") or 0) + 1

    return {
        "project_id": project_id,
        "loop_state": {
            "schema_version": LOOP_STATE_SCHEMA_VERSION,
            "iteration_count": iteration,
            "last_mode": frame.get("mode"),
            "last_action": recommendation.get("action"),
            "last_job_type": (job or {}).get("job_type"),
            "last_result_status": (result or {}).get("status"),
            "result": result or None,
            "last_result": result or prev.get("last_result"),
            "fingerprints": prev.get("fingerprints") or [],
            "pending_jobs": prev.get("pending_jobs") or [],
            "objectives": prev.get("objectives") or [],
            "updated_at": created_at,
        },
    }
