import uuid
from typing import Any

from storage import read_open_loops, update_open_loop_status, write_open_loops


def list_open_loops() -> list[dict[str, Any]]:
    return read_open_loops()


def create_open_loop(title: str, owner: str, priority: str) -> tuple[dict[str, Any], int]:
    rows = read_open_loops()
    item = {
        "id": f"loop-{uuid.uuid4().hex[:8]}",
        "title": title,
        "owner": owner,
        "status": "active",
        "priority": priority,
    }
    rows.insert(0, item)
    write_open_loops(rows)
    return item, len(rows)


def close_open_loop(loop_id: str) -> dict[str, Any] | None:
    return update_open_loop_status(loop_id, "closed")
