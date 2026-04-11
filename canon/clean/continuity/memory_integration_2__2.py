from datetime import datetime, timezone


def _score_memory(item: dict) -> float:
    base = float(item.get("score", 1.0))
    ts = item.get("created_at")
    if not ts:
        return base
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        age_seconds = (datetime.now(timezone.utc) - dt).total_seconds()
        decay = 1 / (1 + (age_seconds / 86400))
        return base * decay
    except Exception:
        return base


def get_relevant_memory(memory_search_fn, project_id: str, limit: int = 5):
    try:
        results = memory_search_fn(project_id=project_id, limit=limit * 3) or []
        scored = [(item, _score_memory(item)) for item in results]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [item for item, _ in scored[:limit]]
    except Exception:
        return []


def build_memory_payload_from_writeback(project_id: str, writeback: dict) -> dict | None:
    if not writeback:
        return None

    wtype = writeback.get("type")
    if wtype not in {"execution_result", "execution_error"}:
        return None

    summary = (writeback.get("summary") or "").strip()
    if not summary:
        return None

    created_at = writeback.get("created_at") or datetime.now(timezone.utc).isoformat()

    return {
        "project_id": project_id,
        "content": summary,
        "kind": wtype,
        "source": "execution_writeback",
        "source_id": writeback.get("id"),
        "created_at": created_at,
        "meta": {
            "job_id": writeback.get("job_id"),
            "type": wtype,
        },
    }


def persist_memory_from_writeback(memory_upsert_fn, project_id: str, writeback: dict):
    payload = build_memory_payload_from_writeback(project_id, writeback)
    if not payload:
        return None
    try:
        return memory_upsert_fn(payload)
    except Exception:
        return None
