import json
import sqlite3
from pathlib import Path
from typing import Any

from services.auth_accounts import DEFAULT_RUNTIME_ACCOUNTS
from services.observability_service import ensure_runtime_dirs

CONTROL_DIR = Path(__file__).resolve().parent
RUNTIME_DIR = CONTROL_DIR.parent
DATA_DIR = RUNTIME_DIR / "data"
DB_PATH = DATA_DIR / "nexus_runtime.db"
JSON_PATH = DATA_DIR / "open_loops.json"
MIGRATIONS_DIR = CONTROL_DIR / "migrations"


def _conn() -> sqlite3.Connection:
    ensure_runtime_dirs()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_migration_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            name TEXT PRIMARY KEY,
            applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )


def _apply_migrations(conn: sqlite3.Connection) -> None:
    _ensure_migration_table(conn)
    applied = {
        row["name"]
        for row in conn.execute("SELECT name FROM schema_migrations").fetchall()
    }

    for path in sorted(MIGRATIONS_DIR.glob("*.sql")):
        if path.name in applied:
            continue
        conn.executescript(path.read_text(encoding="utf-8"))
        conn.execute(
            "INSERT INTO schema_migrations (name) VALUES (?)",
            (path.name,),
        )


def _seed_open_loops(conn: sqlite3.Connection) -> None:
    existing = conn.execute("SELECT COUNT(*) AS c FROM open_loops").fetchone()["c"]
    if existing != 0 or not JSON_PATH.exists():
        return

    raw = json.loads(JSON_PATH.read_text(encoding="utf-8-sig"))
    JSON_PATH.write_text(json.dumps(raw, indent=2), encoding="utf-8")
    for row in raw:
        conn.execute(
            "INSERT OR REPLACE INTO open_loops (id, title, owner, status, priority) VALUES (?, ?, ?, ?, ?)",
            (
                row.get("id"),
                row.get("title", "Untitled open loop"),
                row.get("owner", "Nexus"),
                row.get("status", "active"),
                row.get("priority", "normal"),
            ),
        )


def _seed_runtime_accounts(conn: sqlite3.Connection) -> None:
    existing = conn.execute("SELECT COUNT(*) AS c FROM runtime_accounts").fetchone()["c"]
    if existing != 0:
        return

    for account in DEFAULT_RUNTIME_ACCOUNTS:
        conn.execute(
            "INSERT INTO runtime_accounts (username, role, token, is_active) VALUES (?, ?, ?, ?)",
            (
                account["username"],
                account["role"],
                account["token"],
                account["is_active"],
            ),
        )


def init_db() -> None:
    ensure_runtime_dirs()
    conn = _conn()
    try:
        _apply_migrations(conn)
        _seed_open_loops(conn)
        _seed_runtime_accounts(conn)
        conn.commit()
    finally:
        conn.close()


def read_open_loops() -> list[dict[str, Any]]:
    init_db()
    conn = _conn()
    try:
        rows = conn.execute(
            "SELECT id, title, owner, status, priority FROM open_loops ORDER BY rowid DESC"
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def write_open_loops(rows: list[dict[str, Any]]) -> None:
    init_db()
    conn = _conn()
    try:
        conn.execute("DELETE FROM open_loops")
        for row in rows:
            conn.execute(
                "INSERT OR REPLACE INTO open_loops (id, title, owner, status, priority) VALUES (?, ?, ?, ?, ?)",
                (
                    row.get("id"),
                    row.get("title", "Untitled open loop"),
                    row.get("owner", "Nexus"),
                    row.get("status", "active"),
                    row.get("priority", "normal"),
                ),
            )
        conn.commit()
    finally:
        conn.close()


def update_open_loop_status(loop_id: str, status: str) -> dict[str, Any] | None:
    init_db()
    conn = _conn()
    try:
        row = conn.execute(
            "SELECT id, title, owner, status, priority FROM open_loops WHERE id = ?",
            (loop_id,),
        ).fetchone()
        if row is None:
            return None
        conn.execute(
            "UPDATE open_loops SET status = ? WHERE id = ?",
            (status, loop_id),
        )
        conn.commit()
        updated = dict(row)
        updated["status"] = status
        return updated
    finally:
        conn.close()


def get_storage_status() -> dict[str, Any]:
    init_db()
    conn = _conn()
    try:
        open_loops = conn.execute("SELECT COUNT(*) AS c FROM open_loops").fetchone()["c"]
        migrations = conn.execute("SELECT COUNT(*) AS c FROM schema_migrations").fetchone()["c"]
        accounts = conn.execute("SELECT COUNT(*) AS c FROM runtime_accounts WHERE is_active = 1").fetchone()["c"]
        sessions = conn.execute(
            "SELECT COUNT(*) AS c FROM runtime_sessions WHERE revoked_at IS NULL AND expires_at > strftime('%s','now')"
        ).fetchone()["c"]
        return {
            "database_path": str(DB_PATH),
            "open_loop_count": open_loops,
            "applied_migration_count": migrations,
            "active_account_count": accounts,
            "active_session_count": sessions,
        }
    finally:
        conn.close()


def check_storage_ready() -> dict[str, Any]:
    status = get_storage_status()
    return {
        "ready": True,
        "database_path": status["database_path"],
        "open_loop_count": status["open_loop_count"],
        "applied_migration_count": status["applied_migration_count"],
        "active_account_count": status["active_account_count"],
        "active_session_count": status["active_session_count"],
    }


def read_runtime_accounts() -> list[dict[str, Any]]:
    init_db()
    conn = _conn()
    try:
        rows = conn.execute(
            """
            SELECT username, role, token, is_active
            FROM runtime_accounts
            ORDER BY username ASC
            """
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def update_runtime_account_active(username: str, is_active: int) -> dict[str, Any] | None:
    init_db()
    conn = _conn()
    try:
        row = conn.execute(
            """
            SELECT username, role, token, is_active
            FROM runtime_accounts
            WHERE username = ?
            """,
            (username,),
        ).fetchone()
        if row is None:
            return None
        conn.execute(
            "UPDATE runtime_accounts SET is_active = ? WHERE username = ?",
            (is_active, username),
        )
        conn.commit()
        updated = dict(row)
        updated["is_active"] = is_active
        return updated
    finally:
        conn.close()


def create_runtime_session(
    session_id: str,
    username: str,
    token: str,
    created_at: int,
    expires_at: int,
) -> dict[str, Any]:
    init_db()
    conn = _conn()
    try:
        conn.execute(
            """
            INSERT INTO runtime_sessions (id, username, token, created_at, expires_at, revoked_at)
            VALUES (?, ?, ?, ?, ?, NULL)
            """,
            (session_id, username, token, created_at, expires_at),
        )
        conn.commit()
        return {
            "id": session_id,
            "username": username,
            "token": token,
            "created_at": created_at,
            "expires_at": expires_at,
            "revoked_at": None,
        }
    finally:
        conn.close()


def read_runtime_session_by_token(token: str) -> dict[str, Any] | None:
    init_db()
    conn = _conn()
    try:
        row = conn.execute(
            """
            SELECT
                s.id,
                s.username,
                s.token,
                s.created_at,
                s.expires_at,
                s.revoked_at,
                a.role,
                a.is_active
            FROM runtime_sessions s
            JOIN runtime_accounts a ON a.username = s.username
            WHERE s.token = ?
            """,
            (token,),
        ).fetchone()
        return dict(row) if row is not None else None
    finally:
        conn.close()


def revoke_runtime_session(token: str, revoked_at: int) -> dict[str, Any] | None:
    init_db()
    conn = _conn()
    try:
        row = conn.execute(
            """
            SELECT id, username, token, created_at, expires_at, revoked_at
            FROM runtime_sessions
            WHERE token = ?
            """,
            (token,),
        ).fetchone()
        if row is None:
            return None
        conn.execute(
            "UPDATE runtime_sessions SET revoked_at = ? WHERE token = ?",
            (revoked_at, token),
        )
        conn.commit()
        updated = dict(row)
        updated["revoked_at"] = revoked_at
        return updated
    finally:
        conn.close()


def read_runtime_sessions() -> list[dict[str, Any]]:
    init_db()
    conn = _conn()
    try:
        rows = conn.execute(
            """
            SELECT
                s.id,
                s.username,
                s.created_at,
                s.expires_at,
                s.revoked_at,
                a.role,
                a.is_active
            FROM runtime_sessions s
            JOIN runtime_accounts a ON a.username = s.username
            ORDER BY s.created_at DESC
            """
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def revoke_runtime_session_by_id(session_id: str, revoked_at: int) -> dict[str, Any] | None:
    init_db()
    conn = _conn()
    try:
        row = conn.execute(
            """
            SELECT id, username, token, created_at, expires_at, revoked_at
            FROM runtime_sessions
            WHERE id = ?
            """,
            (session_id,),
        ).fetchone()
        if row is None:
            return None
        conn.execute(
            "UPDATE runtime_sessions SET revoked_at = ? WHERE id = ?",
            (revoked_at, session_id),
        )
        conn.commit()
        updated = dict(row)
        updated["revoked_at"] = revoked_at
        return updated
    finally:
        conn.close()


def delete_expired_runtime_sessions(now_ts: int) -> int:
    init_db()
    conn = _conn()
    try:
        result = conn.execute(
            """
            DELETE FROM runtime_sessions
            WHERE expires_at <= ?
            """,
            (now_ts,),
        )
        conn.commit()
        return int(result.rowcount or 0)
    finally:
        conn.close()
