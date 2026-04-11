from fastapi import APIRouter, Depends, HTTPException

from routes.auth_deps import get_current_user
from schemas.workflow_schema import OpenLoopCreateRequest
from services.observability_service import audit_write
from services.workflow_service import close_open_loop, create_open_loop, list_open_loops

router = APIRouter()


@router.get("/workflows/open-loops")
def get_open_loops(user=Depends(get_current_user)):
    rows = list_open_loops()
    return {"items": rows, "count": len(rows), "actor": {"username": user.username, "role": user.role}}


@router.post("/workflows/open-loops/add")
def add_open_loop(payload: OpenLoopCreateRequest, user=Depends(get_current_user)):
    owner = payload.owner or user.username
    priority = payload.priority or "normal"
    item, count = create_open_loop(payload.title, owner, priority)
    result = {
        "result": "open loop added",
        "item": item,
        "count": count,
        "actor": {"username": user.username, "role": user.role},
    }
    audit_write(result["actor"], "workflow.open_loops.add", {"item_id": item["id"]})
    return result


@router.post("/workflows/open-loops/{loop_id}/close")
def close_workflow_loop(loop_id: str, user=Depends(get_current_user)):
    item = close_open_loop(loop_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Open loop not found")

    result = {
        "result": "open loop closed",
        "item": item,
        "actor": {"username": user.username, "role": user.role},
    }
    audit_write(result["actor"], "workflow.open_loops.close", {"item_id": item["id"]})
    return result
