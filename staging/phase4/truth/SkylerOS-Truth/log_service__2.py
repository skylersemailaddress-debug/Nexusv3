from __future__ import annotations

from pathlib import Path
import os


def tail_logs(limit: int = 100) -> dict:
    log_path = os.getenv("SKYLER_LOG_FILE")

    if not log_path:
        return {"ok": False, "error": "SKYLER_LOG_FILE is not configured"}

    path = Path(log_path).resolve()

    if not path.exists():
        return {"ok": False, "error": f"log file not found: {path}"}

    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception as e:
        return {"ok": False, "error": str(e)}

    return {
        "ok": True,
        "path": str(path),
        "lines": lines[-limit:]
    }
