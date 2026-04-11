def prioritize_objectives(context: dict, base_context: dict) -> list[dict]:
    candidates = []

    user_input = (base_context.get("user_input") or "").strip()
    if user_input:
        candidates.append({
            "type": "user_request",
            "goal": user_input,
            "priority": 100,
        })

    for mem in (context.get("relevant_memory") or []):
        text = mem.get("text", "")
        score = float(mem.get("score") or 0)
        candidates.append({
            "type": "memory_followup",
            "goal": text,
            "priority": int(score * 50),
        })

    if not candidates:
        candidates.append({
            "type": "idle",
            "goal": "no active objective",
            "priority": 0,
        })

    return sorted(candidates, key=lambda x: x["priority"], reverse=True)


def resolve_objective(context: dict, base_context: dict) -> dict:
    """
    Canonical entrypoint used by loop_api.
    Always returns a single selected objective.
    """
    candidates = prioritize_objectives(context, base_context)
    return candidates[0]
