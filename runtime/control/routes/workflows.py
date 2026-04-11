import uuid

from fastapi import APIRouter, Depends

from storage import read_open_loops, write_open_loops
from routes.auth_deps import get_current_user
from services.observability_service import audit_write
from schemas.workflow_schema import OpenLoopCreateRequest

router = APIRouter()

@router.get("/workflows/open-loops")
def get_open_loops(user=Depends(get_current_user)):
    rows = read_open_loops()
    return {"items": rows, "count": len(rows), "actor": {"username": user.username, "role": user.role}}

@router.post("/workflows/open-loops/add")
def add_open_loop(payload: OpenLoopCreateRequest, user=Depends(get_current_user)):
    rows = read_open_loops()
    owner = payload.owner or user.username
    priority = payload.priority or "normal"
    item = {
        "id": f"loop-{uuid.uuid4().hex[:8]}",
        "title": payload.title,
        "owner": owner,
        "status": "active",
        "priority": priority
    }
    rows.insert(0, item)
    write_open_loops(rows)
    result = {
        "result": "open loop added",
        "item": item,
        "count": len(rows),
        "actor": {"username": user.username, "role": user.role}
    }
    audit_write(result["actor"], "workflow.open_loops.add", {"item_id": item["id"]})
    return result
