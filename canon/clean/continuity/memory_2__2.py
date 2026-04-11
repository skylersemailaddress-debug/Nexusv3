from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from app.jsonb import to_jsonb
from app.auth import require_api_token
from app.db import get_conn

router = APIRouter(
    prefix="/memory",
    tags=["memory"],
    dependencies=[Depends(require_api_token)],
)


class MemoryUpsertRequest(BaseModel):
    id: str
    project_id: str | None = None
    scope: str
    title: str
    content: str
    status: str = "active"
    confidence: float = 0.8
    meta: dict = Field(default_factory=dict)


class MemorySearchRequest(BaseModel):
    project_id: str | None = None
    scope: str | None = None
    query: str | None = None
    limit: int = 10


@router.post("/upsert")
def memory_upsert(req: MemoryUpsertRequest):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            '''
            insert into memory_records (id, project_id, scope, title, content, status, confidence, meta)
            values (%s, %s, %s, %s, %s, %s, %s, %s)
            on conflict (id) do update
            set project_id = excluded.project_id,
                scope = excluded.scope,
                title = excluded.title,
                content = excluded.content,
                status = excluded.status,
                confidence = excluded.confidence,
                meta = excluded.meta,
                updated_at = now()
            returning id, project_id, scope, title, content, status, confidence, meta, updated_at
            ''',
            (
                req.id,
                req.project_id,
                req.scope,
                req.title,
                req.content,
                req.status,
                req.confidence,
                to_jsonb(req.meta),
            ),
        )
        row = cur.fetchone()
        conn.commit()
        return {"ok": True, "memory": row}


@router.post("/search")
def memory_search(req: MemorySearchRequest):
    clauses = ["1=1"]
    params = []

    if req.project_id is not None:
        clauses.append("(project_id = %s or project_id is null)")
        params.append(req.project_id)

    if req.scope is not None:
        clauses.append("scope = %s")
        params.append(req.scope)

    if req.query:
        clauses.append("(title ilike %s or content ilike %s)")
        params.append(f"%{req.query}%")
        params.append(f"%{req.query}%")

    params.append(req.limit)

    sql = f'''
        select id, project_id, scope, title, content, status, confidence, meta, updated_at
        from memory_records
        where {" and ".join(clauses)}
        order by updated_at desc
        limit %s
    '''

    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, params)
        rows = cur.fetchall()
        return {"ok": True, "items": rows}

