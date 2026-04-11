from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.auth import require_api_token
from app.services.control_plane import list_runners, set_runner_desired_state
from app.services.rbac import ActorContext, require_role

router = APIRouter(
    prefix="/admin/runners",
    tags=["admin"],
    dependencies=[Depends(require_api_token)],
)


class RunnerStateRequest(BaseModel):
    desired_state: str


@router.get("")
def admin_runner_list(_: ActorContext = Depends(require_role("admin", "operator"))):
    now = datetime.now(timezone.utc)
    items = []
    for runner in list_runners():
        heartbeat = runner.get("last_heartbeat")
        seconds_since = None
        if heartbeat is not None:
            seconds_since = max(0.0, (now - heartbeat).total_seconds())
        items.append(
            {
                **runner,
                "seconds_since_heartbeat": seconds_since,
                "health": "online" if seconds_since is not None and seconds_since < 60 else "stale",
            }
        )
    return {"ok": True, "items": items}


@router.post("/{runner_id}/state")
def admin_runner_state(
    runner_id: str,
    body: RunnerStateRequest,
    actor: ActorContext = Depends(require_role("admin", "operator")),
):
    runner = set_runner_desired_state(runner_id, body.desired_state, actor.actor, actor.role)
    return {"ok": True, "runner": runner}
