from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from psycopg.types.json import Json
from app.auth import require_api_token
from app.db import get_conn

router = APIRouter(
    prefix="/messages",
    tags=["messages"],
    dependencies=[Depends(require_api_token)],
)

ALLOWED_ROLES = {"user", "assistant", "system", "tool", "critic", "planner", "executor", "archivist", "operator"}

class AppendMessageRequest(BaseModel):
    project_id: str
    role: str
    content: str
    meta: dict = Field(default_factory=dict)

@router.post("/append")
def append_message(req: AppendMessageRequest):
    if req.role not in ALLOWED_ROLES:
        raise HTTPException(status_code=400, detail=f"Invalid role: {req.role}")

    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("select id from projects where id = %s", (req.project_id,))
        project = cur.fetchone()
        if not project:
            raise HTTPException(status_code=404, detail=f"Project not found: {req.project_id}")

        cur.execute(
            "select coalesce(max(sequence_no), 0) + 1 as next_sequence_no from messages where project_id = %s",
            (req.project_id,),
        )
        next_sequence_no = cur.fetchone()["next_sequence_no"]

        cur.execute(
            """
            insert into messages (project_id, role, content, content_text, meta, sequence_no)
            values (%s, %s, %s, %s, %s, %s)
            returning id, project_id, role, content_text, meta, sequence_no, created_at
            """,
            (req.project_id, req.role, req.content, req.content, Json(req.meta), next_sequence_no),
        )
        row = cur.fetchone()
        conn.commit()
        return {"ok": True, "message": row}
