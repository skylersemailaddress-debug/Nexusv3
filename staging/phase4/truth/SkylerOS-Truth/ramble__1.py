from datetime import datetime
from uuid import uuid4

from psycopg.types.json import Json

from app.db import get_conn


def _extract_structure(content: str) -> dict:
    tasks = []
    questions = []
    decisions = []
    ideas = []

    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        lower = line.lower()

        if line.endswith("?"):
            questions.append(line)
        elif lower.startswith("todo") or lower.startswith("- [ ]") or lower.startswith("need to ") or lower.startswith("do "):
            tasks.append(line)
        elif lower.startswith("decision") or lower.startswith("decide") or lower.startswith("we should") or lower.startswith("let's "):
            decisions.append(line)
        else:
            ideas.append(line)

    return {
        "tasks": tasks[:20],
        "questions": questions[:20],
        "decisions": decisions[:20],
        "ideas": ideas[:50],
        "counts": {
            "tasks": len(tasks),
            "questions": len(questions),
            "decisions": len(decisions),
            "ideas": len(ideas),
        },
    }


def capture_ramble(project_id: str, content: str, meta: dict | None = None) -> dict:
    meta = meta or {}
    structured = _extract_structure(content)

    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("select id from projects where id = %s", (project_id,))
        project = cur.fetchone()
        if not project:
            raise ValueError(f"Project not found: {project_id}")

        cur.execute(
            "select coalesce(max(sequence_no), 0) + 1 as next_sequence_no from messages where project_id = %s",
            (project_id,),
        )
        next_sequence_no = cur.fetchone()["next_sequence_no"]

        cur.execute(
            """
            insert into messages (project_id, role, content, content_text, meta, sequence_no)
            values (%s, %s, %s, %s, %s, %s)
            returning id, project_id, role, content_text, meta, sequence_no, created_at
            """,
            (
                project_id,
                "user",
                content,
                content,
                Json({"source": "ramble_mode", **meta}),
                next_sequence_no,
            ),
        )
        message_row = cur.fetchone()
        message_id = message_row["id"]

        artifact_id = f"ramble_{uuid4().hex[:16]}"
        title = f"Ramble Capture {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}Z"

        payload = {
            "ok": True,
            "project_id": project_id,
            "captured_at": datetime.utcnow().isoformat() + "Z",
            "message_id": message_id,
            "raw_content": content,
            "structured": structured,
        }

        cur.execute(
            """
            insert into artifacts (id, project_id, kind, title, path, payload, meta)
            values (%s, %s, 'ramble_capture', %s, %s, %s, %s)
            returning id, project_id, kind, title, path, payload, meta, created_at, updated_at
            """,
            (
                artifact_id,
                project_id,
                title,
                None,
                Json(payload),
                Json({"source": "ramble_mode"}),
            ),
        )
        artifact_row = cur.fetchone()
        conn.commit()

    return {
        "ok": True,
        "project_id": project_id,
        "message": message_row,
        "capture": artifact_row,
    }
