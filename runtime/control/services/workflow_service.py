import uuid
from typing import Any

from storage import read_open_loops, write_open_loops

STATUS_ACTIVE = "active"
STATUS_CLOSED = "closed"


def list_open_loops() -> list[dict[str, Any]]:
    return read_open_loops()


def create_open_loop(title: str, owner: str, priority: str) -> tuple[dict[str, Any], int]:
    rows = read_open_loops()
    item = {
        "id": f"loop-{uuid.uuid4().hex[:8]}",
        "title": title,
        "owner": owner,
        "status": STATUS_ACTIVE,
        "priority": priority,
    }
    rows.insert(0, item)
    write_open_loops(rows)
    return item, len(rows)


def _find_loop(rows: list[dict[str, Any]], loop_id: str) -> tuple[int, dict[str, Any]] | None:
    for index, row in enumerate(rows):
        if row.get("id") == loop_id:
            return index, row
    return None


def update_open_loop(
    loop_id: str,
    *,
    title: str | None = None,
    owner: str | None = None,
    priority: str | None = None,
) -> dict[str, Any] | None:
    rows = read_open_loops()
    match = _find_loop(rows, loop_id)
    if match is None:
        return None

    index, row = match
    updated = dict(row)
    if title is not None:
        updated["title"] = title
    if owner is not None:
        updated["owner"] = owner
    if priority is not None:
        updated["priority"] = priority

    rows[index] = updated
    write_open_loops(rows)
    return updated


def _transition_open_loop(loop_id: str, *, from_status: str, to_status: str) -> dict[str, Any] | None:
    rows = read_open_loops()
    match = _find_loop(rows, loop_id)
    if match is None:
        return None

    index, row = match
    current_status = row.get("status", STATUS_ACTIVE)
    if current_status != from_status:
        raise ValueError(f"Invalid workflow transition: {current_status} -> {to_status}")

    updated = dict(row)
    updated["status"] = to_status
    rows[index] = updated
    write_open_loops(rows)
    return updated


def close_open_loop(loop_id: str) -> dict[str, Any] | None:
    return _transition_open_loop(loop_id, from_status=STATUS_ACTIVE, to_status=STATUS_CLOSED)


def reopen_open_loop(loop_id: str) -> dict[str, Any] | None:
    return _transition_open_loop(loop_id, from_status=STATUS_CLOSED, to_status=STATUS_ACTIVE)
