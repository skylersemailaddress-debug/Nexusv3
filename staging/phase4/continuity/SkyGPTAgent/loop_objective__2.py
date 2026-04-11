def resolve_objective(context: dict, base_context: dict) -> dict:
    # 1. new objective from user
    user_input = (base_context.get("user_input") or "").strip()
    if user_input:
        return {
            "type": "user_request",
            "goal": user_input,
        }

    # 2. carry forward prior objective
    prior = (base_context.get("loop_state") or {}).get("objective")
    if prior:
        return prior

    # 3. fallback to memory
    memory = context.get("relevant_memory") or []
    if memory:
        return {
            "type": "memory_followup",
            "goal": memory[0].get("text", ""),
        }

    return {
        "type": "idle",
        "goal": "no active objective",
    }
