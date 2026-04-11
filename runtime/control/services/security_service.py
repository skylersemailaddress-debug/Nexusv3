import time
from collections import defaultdict, deque

from services.env_service import get_runtime_config

_REQUESTS = defaultdict(deque)


def _get_limits() -> tuple[int, int]:
    config = get_runtime_config()
    window_seconds = int(config["rate_limit_window_seconds"])
    max_requests = int(config["rate_limit_max_requests"])
    return window_seconds, max_requests


def allow_request(key: str) -> bool:
    window_seconds, max_requests = _get_limits()
    now = time.time()
    q = _REQUESTS[key]
    while q and (now - q[0]) > window_seconds:
        q.popleft()
    if len(q) >= max_requests:
        return False
    q.append(now)
    return True
