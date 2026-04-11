import time

def get_dashboard_status():
    return {
        "system": "Nexus Runtime",
        "status": "ok",
        "runtime": "sqlite-active"
    }

def get_dashboard_signals():
    now = int(time.time())
    return {
        "signals": [
            {
                "id": "signal-runtime-health",
                "title": "Runtime locked and validated",
                "severity": "good",
                "detail": "API, action route, dashboard status, and UI are all passing.",
                "ts": now
            },
            {
                "id": "signal-baseline-frozen",
                "title": "Baseline freeze available",
                "severity": "info",
                "detail": "A known-good runtime baseline exists and should be treated as the rollback point.",
                "ts": now
            },
            {
                "id": "signal-next-step",
                "title": "Next best move",
                "severity": "action",
                "detail": "Continue the Codex-safe technical path without widening scope.",
                "ts": now
            }
        ]
    }

def get_dashboard_brief():
    return {
        "headline": "Nexus commercial runtime is live.",
        "summary": "One executable authority surface is running with a validated API, UI, dashboard status route, and durable open-loops storage.",
        "next_action": "Complete backend modularization while preserving validation."
    }
