from typing import Dict, Any

def resolve_checkpoint(loop_state: Dict[str, Any], checkpoint: Dict[str, Any]) -> Dict[str, Any]:
    if not checkpoint:
        return loop_state

    # checkpoint fills gaps only (never overrides live)
    merged = dict(loop_state or {})

    for k, v in checkpoint.items():
        if k not in merged or merged[k] in (None, "", []):
            merged[k] = v

    return merged
