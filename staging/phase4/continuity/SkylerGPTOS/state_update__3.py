from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from psycopg.types.json import Json
from app.auth import require_api_token
from app.db import get_conn

router = APIRouter(
    prefix="/projects",
    tags=["state"],
    dependencies=[Depends(require_api_token)],
)

class UpdateStateRequest(BaseModel):
    current_objective_id: str | None = None
    objective_next_step_id: str | None = None
    blocker_ids_open: list[str] | None = None
    meta: dict = Field(default_factory=dict)

@router.post("/{project_id}/state/update")
def update_project_state(project_id: str, req: UpdateStateRequest):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("select id from projects where id = %s", (project_id,))
        project = cur.fetchone()
        if not project:
            raise HTTPException(status_code=404, detail=f"Project not found: {project_id}")

        objective = None
        if req.current_objective_id:
            cur.execute(
                "select id, project_id, title, next_step_id from objectives where id = %s and project_id = %s",
                (req.current_objective_id, project_id),
            )
            objective = cur.fetchone()
            if not objective:
                raise HTTPException(status_code=400, detail="Invalid objective")

        next_step = None
        if req.objective_next_step_id:
            objective_id_for_step = req.current_objective_id or project.get("current_objective_id")
            if not objective_id_for_step:
                raise HTTPException(status_code=400, detail="Missing objective")

            cur.execute(
                "select id, project_id, objective_id, title from next_steps where id = %s and project_id = %s",
                (req.objective_next_step_id, project_id),
            )
            next_step = cur.fetchone()
            if not next_step:
                raise HTTPException(status_code=400, detail="Invalid next step")
            if next_step.get("objective_id") != objective_id_for_step:
                raise HTTPException(status_code=400, detail="Step does not belong to objective")

        if req.current_objective_id:
            cur.execute(
                "update projects set current_objective_id = %s, updated_at = now() where id = %s",
                (req.current_objective_id, project_id),
            )

        if req.current_objective_id and req.objective_next_step_id:
            cur.execute(
                "update objectives set next_step_id = %s, updated_at = now() where id = %s and project_id = %s",
                (req.objective_next_step_id, req.current_objective_id, project_id),
            )

        cur.execute(
            """
            insert into project_state (
                id, project_id, current_objective, next_step, status, structured_state, version_no, updated_at
            )
            values (
                %s, %s, %s, %s, 'active', %s, 1, now()
            )
            on conflict (project_id) do update set
                current_objective = excluded.current_objective,
                next_step = excluded.next_step,
                structured_state = excluded.structured_state,
                version_no = project_state.version_no + 1,
                updated_at = now()
            returning id, project_id, current_objective, next_step, status, structured_state, version_no, updated_at
            """,
            (
                f"state-{project_id}",
                project_id,
                objective["title"] if objective else None,
                next_step["title"] if next_step else None,
                Json(
                    {
                        "current_objective_id": req.current_objective_id,
                        "next_step_id": req.objective_next_step_id,
                        "blocker_ids_open": req.blocker_ids_open or [],
                        "meta": req.meta,
                    }
                ),
            ),
        )
        state_row = cur.fetchone()

        conn.commit()

        return {
            "ok": True,
            "project_id": project_id,
            "current_objective_id": req.current_objective_id,
            "objective_next_step_id": req.objective_next_step_id,
            "meta": req.meta,
            "project_state": state_row,
        }
