from fastapi import APIRouter, Depends

from routes.auth_deps import get_current_user
from services.dashboard_service import (
    get_dashboard_brief,
    get_dashboard_signals,
    get_dashboard_status,
)

router = APIRouter()

@router.get("/dashboard/status")
def dashboard_status(user=Depends(get_current_user)):
    result = get_dashboard_status()
    result["actor"] = {"username": user.username, "role": user.role}
    return result

@router.get("/dashboard/signals")
def dashboard_signals(user=Depends(get_current_user)):
    result = get_dashboard_signals()
    result["actor"] = {"username": user.username, "role": user.role}
    return result

@router.get("/dashboard/brief")
def dashboard_brief(user=Depends(get_current_user)):
    result = get_dashboard_brief()
    result["actor"] = {"username": user.username, "role": user.role}
    return result
