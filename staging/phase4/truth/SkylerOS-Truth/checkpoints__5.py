from datetime import datetime
from uuid import uuid4

from psycopg.types.json import Json

from app.db import get_conn
from app.services.state_builder import get_project_now


def build_checkpoint_payload(project_id: str) -> dict:
    now = get_project_now(project_id)

    if not now.get("ok"):
        return now

    objective = now.get("objective")
    next_step = now.get("next_step")
    blockers = now.get("blockers", [])
    recent_jobs = now.get("recent_jobs", [])
    recent_messages = now.get("recent_messages", [])
    relevant_memory = now.get("relevant_memory", [])

    return {
        "ok": True,
        "project_id": project_id,
        "captured_at": datetime.utcnow().isoformat() + "Z",
        "objective": objective["title"] if objective else None,
        "next_step": next_step["title"] if next_step else None,
        "open_blockers": len(blockers),
        "recent_job_ids": [job["id"] for job in recent_jobs[:5]],
        "memory_signals": [item["title"] for item in relevant_memory[:5]],
        "recent_messages_tail": [
            {
                "role": message["role"],
                "content": message["content"],
                "created_at": str(message["created_at"]),
            }
            for message in recent_messages[-5:]
        ],
    }


def create_checkpoint(project_id: str) -> dict:
    payload = build_checkpoint_payload(project_id)
    if not payload.get("ok"):
        return payload

    checkpoint_id = f"ckpt_{uuid4().hex[:16]}"
    title = f"Checkpoint {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}Z"

    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            insert into artifacts (id, project_id, kind, title, path, payload, meta)
            values (%s, %s, 'checkpoint', %s, %s, %s, %s)
            returning id, project_id, kind, title, path, payload, meta, created_at, updated_at
            """,
            (
                checkpoint_id,
                project_id,
                title,
                None,
                Json(payload),
                Json({"source": "checkpoint_service"}),
            ),
        )
        row = cur.fetchone()
        conn.commit()
        return {"ok": True, "checkpoint": row}
