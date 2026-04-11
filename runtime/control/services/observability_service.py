import json
import time
import uuid
from pathlib import Path
from typing import Any

CONTROL_DIR = Path(__file__).resolve().parent.parent
RUNTIME_DIR = CONTROL_DIR.parent
DATA_DIR = RUNTIME_DIR / "data"
LOG_DIR = RUNTIME_DIR / "logs"
AUDIT_LOG = LOG_DIR / "audit.log"
REQUEST_LOG = LOG_DIR / "requests.log"

def ensure_runtime_dirs():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)

def new_request_id() -> str:
    return f"req-{uuid.uuid4().hex[:12]}"

def append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    ensure_runtime_dirs()
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload) + "\n")

def log_request(payload: dict[str, Any]) -> None:
    append_jsonl(REQUEST_LOG, payload)

def log_audit(payload: dict[str, Any]) -> None:
    append_jsonl(AUDIT_LOG, payload)

def audit_write(actor: dict[str, Any], action: str, detail: dict[str, Any] | None = None) -> None:
    log_audit({
        "ts": int(time.time()),
        "actor": actor,
        "action": action,
        "detail": detail or {}
    })
