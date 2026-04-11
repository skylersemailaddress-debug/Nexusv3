import time
from collections import defaultdict, deque

WINDOW_SECONDS = 60
MAX_REQUESTS_PER_WINDOW = 120
_REQUESTS = defaultdict(deque)

def allow_request(key: str) -> bool:
    now = time.time()
    q = _REQUESTS[key]
    while q and (now - q[0]) > WINDOW_SECONDS:
        q.popleft()
    if len(q) >= MAX_REQUESTS_PER_WINDOW:
        return False
    q.append(now)
    return True
