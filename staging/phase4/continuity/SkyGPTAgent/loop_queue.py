def update_objective_queue(base_context: dict, new_objective: dict) -> list[dict]:
    prior = (base_context.get("loop_state") or {}).get("objectives") or []
    queue = [dict(item) for item in prior]

    if new_objective and new_objective.get("type") == "user_request":
        goal = new_objective["goal"]
        if not any(obj.get("goal") == goal for obj in queue):
            queue.insert(0, {
                "goal": goal,
                "status": "pending",
                "attempts": 0,
            })

    for obj in queue:
        obj.setdefault("status", "pending")
        obj.setdefault("attempts", 0)

    return queue


def select_active_objective(queue: list[dict]) -> dict:
    for obj in queue:
        if obj.get("status") in ["pending", "active"]:
            obj["status"] = "active"
            return obj

    return {
        "goal": "no active objective",
        "status": "idle",
        "attempts": 0,
    }
