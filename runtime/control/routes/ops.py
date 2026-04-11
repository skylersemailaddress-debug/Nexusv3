from pathlib import Path
import time

from fastapi import APIRouter, Depends, HTTPException

from routes.auth_deps import require_admin
from services.auth_service import (
    activate_runtime_account,
    cleanup_expired_sessions,
    deactivate_runtime_account,
    list_runtime_account_summaries,
    list_runtime_session_summaries,
    revoke_session_by_id,
    revoke_sessions_for_username,
)
from services.observability_service import (
    AUDIT_LOG,
    EVENT_LOG,
    REQUEST_LOG,
    audit_write,
    get_observability_status,
    record_event,
)

router = APIRouter()


@router.get("/ops/support-bundle")
def support_bundle(user=Depends(require_admin)):
    def tail_lines(path: Path, limit: int = 20):
        if not path.exists():
            return []
        lines = path.read_text(encoding="utf-8").splitlines()
        return lines[-limit:]

    actor = {"username": user.username, "role": user.role}
    record_event("ops.support_bundle.read", actor=actor)
    return {
        "generated_at": int(time.time()),
        "actor": actor,
        "request_log_tail": tail_lines(REQUEST_LOG),
        "audit_log_tail": tail_lines(AUDIT_LOG),
        "event_log_tail": tail_lines(EVENT_LOG),
        "observability": get_observability_status(),
    }


@router.get("/ops/observability/status")
def observability_status(user=Depends(require_admin)):
    actor = {"username": user.username, "role": user.role}
    status = get_observability_status()
    record_event("ops.observability.status.read", actor=actor)
    return {
        "generated_at": int(time.time()),
        "actor": actor,
        "observability": status,
    }


@router.get("/ops/accounts")
def list_runtime_accounts(user=Depends(require_admin)):
    accounts = list_runtime_account_summaries()
    actor = {"username": user.username, "role": user.role}
    record_event("ops.accounts.read", actor=actor, detail={"count": len(accounts)})
    return {
        "generated_at": int(time.time()),
        "actor": actor,
        "items": accounts,
        "count": len(accounts),
    }


@router.post("/ops/accounts/{username}/deactivate")
def deactivate_account(username: str, user=Depends(require_admin)):
    try:
        item = deactivate_runtime_account(username)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if item is None:
        raise HTTPException(status_code=404, detail="Runtime account not found")
    actor = {"username": user.username, "role": user.role}
    result = {
        "result": "runtime account deactivated",
        "item": {"username": item["username"], "role": item["role"], "is_active": item["is_active"]},
        "actor": actor,
    }
    audit_write(actor, "ops.accounts.deactivate", {"username": username, "role": item["role"]})
    record_event("ops.accounts.deactivate", actor=actor, detail={"username": username, "role": item["role"]})
    return result


@router.post("/ops/accounts/{username}/activate")
def activate_account(username: str, user=Depends(require_admin)):
    try:
        item = activate_runtime_account(username)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if item is None:
        raise HTTPException(status_code=404, detail="Runtime account not found")
    actor = {"username": user.username, "role": user.role}
    result = {
        "result": "runtime account activated",
        "item": {"username": item["username"], "role": item["role"], "is_active": item["is_active"]},
        "actor": actor,
    }
    audit_write(actor, "ops.accounts.activate", {"username": username, "role": item["role"]})
    record_event("ops.accounts.activate", actor=actor, detail={"username": username, "role": item["role"]})
    return result


@router.post("/ops/accounts/{username}/sessions/revoke")
def revoke_account_sessions(username: str, user=Depends(require_admin)):
    item = revoke_sessions_for_username(username)
    if item is None:
        raise HTTPException(status_code=404, detail="Runtime account not found")
    actor = {"username": user.username, "role": user.role}
    result = {
        "result": "runtime account sessions revoked",
        "item": item,
        "actor": actor,
    }
    audit_write(
        actor,
        "ops.accounts.sessions.revoke",
        {"username": username, "revoked_count": item["revoked_count"]},
    )
    record_event("ops.accounts.sessions.revoke", actor=actor, detail={"username": username, "revoked_count": item["revoked_count"]})
    return result


@router.get("/ops/sessions")
def list_runtime_sessions(user=Depends(require_admin)):
    sessions = list_runtime_session_summaries()
    actor = {"username": user.username, "role": user.role}
    record_event("ops.sessions.read", actor=actor, detail={"count": len(sessions)})
    return {
        "generated_at": int(time.time()),
        "actor": actor,
        "items": sessions,
        "count": len(sessions),
    }


@router.post("/ops/sessions/{session_id}/revoke")
def revoke_runtime_session_route(session_id: str, user=Depends(require_admin)):
    try:
        item = revoke_session_by_id(session_id)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if item is None:
        raise HTTPException(status_code=404, detail="Runtime session not found")
    actor = {"username": user.username, "role": user.role}
    result = {
        "result": "runtime session revoked",
        "item": {
            "id": item["id"],
            "username": item["username"],
            "expires_at": item["expires_at"],
            "revoked_at": item["revoked_at"],
        },
        "actor": actor,
    }
    audit_write(
        actor,
        "ops.sessions.revoke",
        {
            "session_id": session_id,
            "username": item["username"],
            "expires_at": item["expires_at"],
            "revoked_at": item["revoked_at"],
        },
    )
    record_event("ops.sessions.revoke", actor=actor, detail={"session_id": session_id, "username": item["username"]})
    return result


@router.post("/ops/sessions/cleanup-expired")
def cleanup_runtime_sessions(user=Depends(require_admin)):
    result = cleanup_expired_sessions()
    actor = {"username": user.username, "role": user.role}
    payload = {
        "result": "ended runtime sessions cleaned",
        "deleted_count": result["deleted_count"],
        "expired_deleted_count": result["expired_deleted_count"],
        "revoked_deleted_count": result["revoked_deleted_count"],
        "retention_seconds": result["retention_seconds"],
        "actor": actor,
    }
    audit_write(
        actor,
        "ops.sessions.cleanup_expired",
        {
            "deleted_count": result["deleted_count"],
            "expired_deleted_count": result["expired_deleted_count"],
            "revoked_deleted_count": result["revoked_deleted_count"],
            "retention_seconds": result["retention_seconds"],
        },
    )
    record_event("ops.sessions.cleanup_expired", actor=actor, detail={"deleted_count": result["deleted_count"]})
    return payload
