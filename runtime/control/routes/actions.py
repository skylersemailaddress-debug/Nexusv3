from fastapi import APIRouter, Depends

from services.actions_service import run_refresh_action, run_test_action
from services.observability_service import audit_write, record_event
from routes.auth_deps import get_current_user, require_admin
from schemas.action_schema import ActionPayload

router = APIRouter()


@router.post("/action/test")
def action_test(payload: ActionPayload, user=Depends(get_current_user)):
    result = run_test_action(payload.model_dump())
    actor = {"username": user.username, "role": user.role}
    result["actor"] = actor
    audit_write(actor, "action.test", {"payload": payload.model_dump()})
    record_event("action.test.executed", actor=actor, detail={"payload": payload.model_dump()})
    return result


@router.post("/action/refresh")
def action_refresh(payload: ActionPayload, user=Depends(get_current_user)):
    result = run_refresh_action(payload.model_dump())
    actor = {"username": user.username, "role": user.role}
    result["actor"] = actor
    audit_write(actor, "action.refresh", {"payload": payload.model_dump()})
    record_event("action.refresh.executed", actor=actor, detail={"payload": payload.model_dump()})
    return result


@router.post("/action/admin/ping")
def action_admin_ping(user=Depends(require_admin)):
    actor = {"username": user.username, "role": user.role}
    result = {"result": "admin ok", "actor": actor}
    audit_write(actor, "action.admin.ping", {})
    record_event("action.admin.ping", actor=actor)
    return result
