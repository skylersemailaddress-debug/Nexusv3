from fastapi import APIRouter, Depends, HTTPException

from routes.auth_deps import get_current_user
from schemas.workflow_schema import OpenLoopCreateRequest, OpenLoopUpdateRequest
from services.observability_service import audit_write, record_event
from services.workflow_service import (
    close_open_loop,
    create_open_loop,
    list_open_loops,
    reopen_open_loop,
    update_open_loop,
)

router = APIRouter()


@router.get("/workflows/open-loops")
def get_open_loops(user=Depends(get_current_user)):
    rows = list_open_loops()
    actor = {"username": user.username, "role": user.role}
    record_event("workflow.open_loops.read", actor=actor, detail={"count": len(rows)})
    return {"items": rows, "count": len(rows), "actor": actor}


@router.post("/workflows/open-loops/add")
def add_open_loop(payload: OpenLoopCreateRequest, user=Depends(get_current_user)):
    owner = payload.owner or user.username
    priority = payload.priority or "normal"
    item, count = create_open_loop(payload.title, owner, priority)
    actor = {"username": user.username, "role": user.role}
    result = {
        "result": "open loop added",
        "item": item,
        "count": count,
        "actor": actor,
    }
    audit_write(actor, "workflow.open_loops.add", {"item_id": item["id"]})
    record_event("workflow.open_loops.add", actor=actor, detail={"item_id": item["id"], "count": count})
    return result


@router.post("/workflows/open-loops/{loop_id}/update")
def update_workflow_loop(loop_id: str, payload: OpenLoopUpdateRequest, user=Depends(get_current_user)):
    item = update_open_loop(
        loop_id,
        title=payload.title,
        owner=payload.owner,
        priority=payload.priority,
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Open loop not found")

    actor = {"username": user.username, "role": user.role}
    result = {
        "result": "open loop updated",
        "item": item,
        "actor": actor,
    }
    audit_write(actor, "workflow.open_loops.update", {"item_id": item["id"]})
    record_event("workflow.open_loops.update", actor=actor, detail={"item_id": item["id"]})
    return result


@router.post("/workflows/open-loops/{loop_id}/close")
def close_workflow_loop(loop_id: str, user=Depends(get_current_user)):
    try:
        item = close_open_loop(loop_id)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if item is None:
        raise HTTPException(status_code=404, detail="Open loop not found")

    actor = {"username": user.username, "role": user.role}
    result = {
        "result": "open loop closed",
        "item": item,
        "actor": actor,
    }
    audit_write(actor, "workflow.open_loops.close", {"item_id": item["id"]})
    record_event("workflow.open_loops.close", actor=actor, detail={"item_id": item["id"]})
    return result


@router.post("/workflows/open-loops/{loop_id}/reopen")
def reopen_workflow_loop(loop_id: str, user=Depends(get_current_user)):
    try:
        item = reopen_open_loop(loop_id)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if item is None:
        raise HTTPException(status_code=404, detail="Open loop not found")

    actor = {"username": user.username, "role": user.role}
    result = {
        "result": "open loop reopened",
        "item": item,
        "actor": actor,
    }
    audit_write(actor, "workflow.open_loops.reopen", {"item_id": item["id"]})
    record_event("workflow.open_loops.reopen", actor=actor, detail={"item_id": item["id"]})
    return result
