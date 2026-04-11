from fastapi import APIRouter
from pydantic import BaseModel
from app.db import get_conn

router = APIRouter(prefix="/projects", tags=["state"])


class UpdateStateRequest(BaseModel):
    current_objective_id: str | None = None
    objective_next_step_id: str | None = None
    blocker_ids_open: list[str] | None = None
    meta: dict = {}


@router.post("/{project_id}/state/update")
def update_project_state(project_id: str, req: UpdateStateRequest):
    with get_conn() as conn, conn.cursor() as cur:
        if req.current_objective_id:
            cur.execute(
                """
                update projects
                set current_objective_id = %s,
                    updated_at = now()
                where id = %s
                """,
                (req.current_objective_id, project_id),
            )

        if req.current_objective_id and req.objective_next_step_id:
            cur.execute(
                """
                update objectives
                set next_step_id = %s,
                    updated_at = now()
                where id = %s and project_id = %s
                """,
                (req.objective_next_step_id, req.current_objective_id, project_id),
            )

        conn.commit()

        return {
            "ok": True,
            "project_id": project_id,
            "current_objective_id": req.current_objective_id,
            "objective_next_step_id": req.objective_next_step_id,
            "meta": req.meta,
        }
