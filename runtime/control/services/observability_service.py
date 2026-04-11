import json
import time
import uuid
from contextvars import ContextVar
from pathlib import Path
from typing import Any

CONTROL_DIR = Path(__file__).resolve().parent.parent
RUNTIME_DIR = CONTROL_DIR.parent
DATA_DIR = RUNTIME_DIR / "data"
LOG_DIR = RUNTIME_DIR / "logs"
AUDIT_LOG = LOG_DIR / "audit.log"
REQUEST_LOG = LOG_DIR / "requests.log"
EVENT_LOG = LOG_DIR / "events.log"

_REQUEST_CONTEXT: ContextVar[dict[str, Any] | None] = ContextVar("request_context", default=None)


def ensure_runtime_dirs():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)


def new_request_id() -> str:
    return f"req-{uuid.uuid4().hex[:12]}"


def append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    ensure_runtime_dirs()
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload) + "\n")


def set_request_context(context: dict[str, Any]) -> object:
    return _REQUEST_CONTEXT.set(context)


def clear_request_context(token: object) -> None:
    _REQUEST_CONTEXT.reset(token)


def get_request_context() -> dict[str, Any]:
    return dict(_REQUEST_CONTEXT.get() or {})


def _with_request_context(payload: dict[str, Any]) -> dict[str, Any]:
    context = get_request_context()
    if not context:
        return payload
    enriched = dict(payload)
    enriched["request"] = context
    return enriched


def log_request(payload: dict[str, Any]) -> None:
    append_jsonl(REQUEST_LOG, _with_request_context(payload))


def log_audit(payload: dict[str, Any]) -> None:
    append_jsonl(AUDIT_LOG, _with_request_context(payload))


def log_event(payload: dict[str, Any]) -> None:
    append_jsonl(EVENT_LOG, _with_request_context(payload))


def audit_write(actor: dict[str, Any], action: str, detail: dict[str, Any] | None = None) -> None:
    log_audit({
        "ts": int(time.time()),
        "actor": actor,
        "action": action,
        "detail": detail or {},
    })


def record_event(
    event_type: str,
    *,
    actor: dict[str, Any] | None = None,
    detail: dict[str, Any] | None = None,
    status: str = "ok",
) -> None:
    log_event({
        "ts": int(time.time()),
        "event_type": event_type,
        "status": status,
        "actor": actor or {},
        "detail": detail or {},
    })
