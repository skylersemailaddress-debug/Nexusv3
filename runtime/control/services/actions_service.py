import time

def run_test_action(payload=None):
    return {
        "result": "working",
        "received": payload or {},
        "timestamp": int(time.time())
    }

def run_refresh_action(payload=None):
    return {
        "result": "dashboard refreshed",
        "received": payload or {},
        "refreshed_at": int(time.time())
    }
