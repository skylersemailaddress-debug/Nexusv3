from fastapi import APIRouter, Depends

from routes.auth_deps import get_current_user
from services.dashboard_service import (
    get_dashboard_brief,
    get_dashboard_signals,
    get_dashboard_status,
)
from services.observability_service import record_event

router = APIRouter()


@router.get("/dashboard/status")
def dashboard_status(user=Depends(get_current_user)):
    result = get_dashboard_status()
    actor = {"username": user.username, "role": user.role}
    result["actor"] = actor
    record_event("dashboard.status.read", actor=actor, detail={"runtime": result.get("runtime")})
    return result


@router.get("/dashboard/signals")
def dashboard_signals(user=Depends(get_current_user)):
    result = get_dashboard_signals()
    actor = {"username": user.username, "role": user.role}
    result["actor"] = actor
    record_event("dashboard.signals.read", actor=actor, detail={"signal_count": len(result.get("signals", []))})
    return result


@router.get("/dashboard/brief")
def dashboard_brief(user=Depends(get_current_user)):
    result = get_dashboard_brief()
    actor = {"username": user.username, "role": user.role}
    result["actor"] = actor
    record_event("dashboard.brief.read", actor=actor)
    return result
