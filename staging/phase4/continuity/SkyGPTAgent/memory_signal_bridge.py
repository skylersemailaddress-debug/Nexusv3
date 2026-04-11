from typing import Any

def summarize_memory_signals(memory_records: list[dict[str, Any]]) -> list[str]:
    signals: list[str] = []
    seen: set[str] = set()
    for record in memory_records or []:
        title = (record.get("title") or "").strip()
        content = (record.get("content") or "").strip()
        candidate = title or content[:120]
        key = candidate.lower()
        if candidate and key not in seen:
            signals.append(candidate)
            seen.add(key)
    return signals[:10]
