import json
import time
import uuid
from contextvars import ContextVar
from pathlib import Path
from typing import Any

from services.env_service import get_runtime_config

CONTROL_DIR = Path(__file__).resolve().parent.parent
RUNTIME_DIR = CONTROL_DIR.parent
DATA_DIR = RUNTIME_DIR / "data"
LOG_DIR = RUNTIME_DIR / "logs"
AUDIT_LOG = LOG_DIR / "audit.log"
REQUEST_LOG = LOG_DIR / "requests.log"
EVENT_LOG = LOG_DIR / "events.log"
OBSERVABILITY_LOGS = {
    "requests": REQUEST_LOG,
    "audit": AUDIT_LOG,
    "events": EVENT_LOG,
}

_REQUEST_CONTEXT: ContextVar[dict[str, Any] | None] = ContextVar("request_context", default=None)
_SENSITIVE_KEYS = {"authorization", "token", "access_token", "refresh_token"}


def ensure_runtime_dirs():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)


def new_request_id() -> str:
    return f"req-{uuid.uuid4().hex[:12]}"


def _observability_limits() -> tuple[int, int]:
    config = get_runtime_config()
    return int(config["observability_log_max_bytes"]), int(config["observability_log_max_files"])


def _archive_path(path: Path, index: int) -> Path:
    return path.with_name(f"{path.name}.{index}")


def _rotate_log_if_needed(path: Path) -> None:
    max_bytes, max_files = _observability_limits()
    if max_bytes <= 0 or max_files <= 0 or not path.exists() or path.stat().st_size < max_bytes:
        return

    oldest = _archive_path(path, max_files)
    if oldest.exists():
        oldest.unlink()

    for index in range(max_files - 1, 0, -1):
        current = _archive_path(path, index)
        if current.exists():
            current.replace(_archive_path(path, index + 1))

    path.replace(_archive_path(path, 1))


def _sanitize_value(value: Any, *, key: str | None = None) -> Any:
    if isinstance(value, dict):
        return {sub_key: _sanitize_value(sub_value, key=sub_key) for sub_key, sub_value in value.items()}
    if isinstance(value, list):
        return [_sanitize_value(item) for item in value]
    if isinstance(value, str):
        if key is not None and key.lower() in _SENSITIVE_KEYS:
            return "[REDACTED]"
        if value.lower().startswith("bearer "):
            return "Bearer [REDACTED]"
        return value
    return value


def append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    ensure_runtime_dirs()
    _rotate_log_if_needed(path)
    sanitized_payload = _sanitize_value(payload)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(sanitized_payload) + "\n")


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


def get_observability_status() -> dict[str, Any]:
    max_bytes, max_files = _observability_limits()
    files = {}
    for name, path in OBSERVABILITY_LOGS.items():
        archives = []
        for index in range(1, max_files + 1):
            archive = _archive_path(path, index)
            if archive.exists():
                archives.append({"name": archive.name, "size_bytes": archive.stat().st_size})
        files[name] = {
            "name": path.name,
            "exists": path.exists(),
            "size_bytes": path.stat().st_size if path.exists() else 0,
            "archive_count": len(archives),
            "archives": archives,
        }
    return {
        "log_dir": str(LOG_DIR),
        "rotation": {"max_bytes": max_bytes, "max_files": max_files},
        "files": files,
    }
