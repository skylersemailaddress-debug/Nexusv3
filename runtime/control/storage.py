from services.observability_service import ensure_runtime_dirs
import json
import sqlite3
from pathlib import Path
from typing import Any

CONTROL_DIR = Path(__file__).resolve().parent
RUNTIME_DIR = CONTROL_DIR.parent
DATA_DIR = RUNTIME_DIR / "data"
DB_PATH = DATA_DIR / "nexus_runtime.db"
JSON_PATH = DATA_DIR / "open_loops.json"

def _conn() -> sqlite3.Connection:
    ensure_runtime_dirs()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db() -> None:
    ensure_runtime_dirs()
    conn = _conn()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS open_loops (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                owner TEXT NOT NULL,
                status TEXT NOT NULL,
                priority TEXT NOT NULL
            )
            """
        )
        conn.commit()

        existing = conn.execute("SELECT COUNT(*) AS c FROM open_loops").fetchone()["c"]
        if existing == 0 and JSON_PATH.exists():
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


