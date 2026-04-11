from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.jsonb import to_jsonb
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
    next_step: str | None = None
    blocker_ids_open: list[str] | None = None
    meta: dict | None = None


def _build_projection_payload(req: UpdateStateRequest) -> dict:
    structured_state: dict = {}

    if req.current_objective_id is not None:
        structured_state["current_objective_id"] = req.current_objective_id

    if req.objective_next_step_id is not None:
        structured_state["next_step_id"] = req.objective_next_step_id

    if req.blocker_ids_open is not None:
        structured_state["blocker_ids_open"] = req.blocker_ids_open

    if req.meta is not None:
        structured_state["meta"] = req.meta

    return structured_state


@router.post("/{project_id}/state/update")
def update_project_state(project_id: str, req: UpdateStateRequest):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("select id, current_objective_id from projects where id = %s", (project_id,))
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

        # Keep relational state in sync when a direct next_step title is provided.
        if req.next_step is not None:
            step_id_to_update = None

            cur.execute("select structured_state from project_state where project_id = %s", (project_id,))
            current_state = cur.fetchone() or {}
            current_structured = current_state.get("structured_state") or {}

            if req.objective_next_step_id:
                step_id_to_update = req.objective_next_step_id
            elif current_structured.get("next_step_id"):
                step_id_to_update = current_structured.get("next_step_id")
            elif objective and objective.get("next_step_id"):
                step_id_to_update = objective.get("next_step_id")
            elif project.get("current_objective_id"):
                cur.execute(
                    "select next_step_id from objectives where id = %s and project_id = %s",
                    (project.get("current_objective_id"), project_id),
                )
                row = cur.fetchone()
                if row:
                    step_id_to_update = row.get("next_step_id")

            if step_id_to_update:
                cur.execute(
                    "update next_steps set title = %s, updated_at = now() where id = %s and project_id = %s",
                    (req.next_step, step_id_to_update, project_id),
                )

        structured_state = _build_projection_payload(req)

        current_objective_title = objective["title"] if objective else None
        next_step_title = req.next_step if req.next_step is not None else (next_step["title"] if next_step else None)

        cur.execute(
            """
            insert into project_state (
                id, project_id, current_objective, next_step, status, structured_state, version_no, updated_at
            )
            values (
                %s, %s, %s, %s, 'active', %s, 1, now()
            )
            on conflict (project_id) do update set
                current_objective = coalesce(excluded.current_objective, project_state.current_objective),
                next_step = coalesce(excluded.next_step, project_state.next_step),
                structured_state = coalesce(project_state.structured_state, '{}'::jsonb) || excluded.structured_state,
                version_no = project_state.version_no + 1,
                updated_at = now()
            returning id, project_id, current_objective, next_step, status, structured_state, version_no, updated_at
            """,
            (
                f"state-{project_id}",
                project_id,
                current_objective_title,
                next_step_title,
                to_jsonb(structured_state),
            ),
        )
        state_row = cur.fetchone()

        conn.commit()

        return {
            "ok": True,
            "project_id": project_id,
            "current_objective_id": req.current_objective_id,
            "objective_next_step_id": req.objective_next_step_id,
            "meta": req.meta or {},
            "project_state": state_row,
        }

