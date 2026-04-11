from typing import List, Dict, Any

def resolve_memory(
    live_context: Dict[str, Any],
    loop_state: Dict[str, Any],
    memory: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    # Priority is enforced by caller; this function only filters + orders memory

    if not memory:
        return []

    # sort by score then recency if present
    def score(m):
        return (
            m.get("score", 0),
            m.get("created_at", "")
        )

    memory_sorted = sorted(memory, key=score, reverse=True)

    # limit working set (buffer)
    return memory_sorted[:20]
