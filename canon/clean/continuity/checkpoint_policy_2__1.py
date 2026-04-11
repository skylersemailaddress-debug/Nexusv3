from typing import Any

def should_checkpoint(message_count: int, memory_count: int) -> bool:
    return message_count >= 25 or memory_count >= 10

def compression_summary(messages: list[dict[str, Any]]) -> dict[str, Any]:
    recent = messages[-10:] if messages else []
    return {
        "ok": True,
        "recent_count": len(recent),
        "summary": "Checkpoint scaffold active. Replace with real summarization logic."
    }
