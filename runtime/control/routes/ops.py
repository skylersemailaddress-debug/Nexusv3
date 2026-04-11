from pathlib import Path
import time

from fastapi import APIRouter, Depends, HTTPException

from routes.auth_deps import require_admin
from services.auth_service import (
    activate_runtime_account,
    deactivate_runtime_account,
    list_runtime_account_summaries,
)
from services.observability_service import AUDIT_LOG, REQUEST_LOG, audit_write

router = APIRouter()


@router.get("/ops/support-bundle")
def support_bundle(user=Depends(require_admin)):
    def tail_lines(path: Path, limit: int = 20):
        if not path.exists():
            return []
        lines = path.read_text(encoding="utf-8").splitlines()
        return lines[-limit:]

    return {
        "generated_at": int(time.time()),
        "actor": {"username": user.username, "role": user.role},
        "request_log_tail": tail_lines(REQUEST_LOG),
        "audit_log_tail": tail_lines(AUDIT_LOG),
    }


@router.get("/ops/accounts")
def list_runtime_accounts(user=Depends(require_admin)):
    accounts = list_runtime_account_summaries()
    return {
        "generated_at": int(time.time()),
        "actor": {"username": user.username, "role": user.role},
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
    result = {
        "result": "runtime account deactivated",
        "item": {"username": item["username"], "role": item["role"], "is_active": item["is_active"]},
        "actor": {"username": user.username, "role": user.role},
    }
    audit_write(result["actor"], "ops.accounts.deactivate", {"username": username})
    return result


@router.post("/ops/accounts/{username}/activate")
def activate_account(username: str, user=Depends(require_admin)):
    try:
        item = activate_runtime_account(username)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if item is None:
        raise HTTPException(status_code=404, detail="Runtime account not found")
    result = {
        "result": "runtime account activated",
        "item": {"username": item["username"], "role": item["role"], "is_active": item["is_active"]},
        "actor": {"username": user.username, "role": user.role},
    }
    audit_write(result["actor"], "ops.accounts.activate", {"username": username})
    return result
