from fastapi import APIRouter

from app.bootstrap import get_bootstrap_status
from app.db import get_conn
from app.settings import settings

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
def health():
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("select current_database() as database_name")
        row = cur.fetchone()

    return {
        "ok": True,
        "app": settings.app_name,
        "database_name": row["database_name"],
        "bootstrap": get_bootstrap_status(),
    }


@router.get("/protected")
def protected_health():
    return {
        "ok": True,
        "protected": True,
    }


@router.get("/system/check")
def system_check():
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("select current_database() as database_name")
        database_name = cur.fetchone()["database_name"]

        cur.execute("select id from projects order by id")
        projects = [row["id"] for row in cur.fetchall()]

        cur.execute("select count(*) as count from jobs")
        job_count = cur.fetchone()["count"]

        cur.execute("select count(*) as count from messages")
        message_count = cur.fetchone()["count"]

    bootstrap = get_bootstrap_status()
    return {
        "ok": bootstrap.get("ok", False) and settings.canonical_db_name == database_name,
        "database_name": database_name,
        "canonical_db_name": settings.canonical_db_name,
        "projects": projects,
        "expected_project": "default",
        "default_project_present": "default" in projects,
        "job_count": job_count,
        "message_count": message_count,
        "bootstrap": bootstrap,
    }
