from app.db import get_conn


def list_artifacts(project_id: str | None = None, kind: str | None = None, limit: int = 50) -> dict:
    clauses = []
    params: list[object] = []
    if project_id:
        clauses.append("project_id = %s")
        params.append(project_id)
    if kind:
        clauses.append("kind = %s")
        params.append(kind)
    where_sql = f"where {' and '.join(clauses)}" if clauses else ""
    params.append(limit)
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            f"""
            select id, project_id, kind, title, path, payload, meta, created_at, updated_at
            from artifacts
            {where_sql}
            order by created_at desc
            limit %s
            """,
            params,
        )
        items = cur.fetchall()
    return {"ok": True, "items": items}
