import json, os

QUEUE = "runtime/queue/lease_queue.json"
RESULTS = "runtime/results/execution_results.json"
SUMMARY = "runtime/results/execution_summary.json"
WORKERS = "runtime/state/worker_registry.json"

def load(path):
    if not os.path.exists(path): return {}
    with open(path) as f: return json.load(f)

def build_state():
    return {
        "queue": load(QUEUE),
        "results": load(RESULTS),
        "summary": load(SUMMARY),
        "workers": load(WORKERS)
    }

if __name__ == "__main__":
    print(json.dumps(build_state(), indent=2))
