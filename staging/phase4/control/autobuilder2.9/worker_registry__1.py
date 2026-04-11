import json, time, os

REGISTRY = "runtime/state/worker_registry.json"

def load():
    if not os.path.exists(REGISTRY): return {}
    with open(REGISTRY) as f: return json.load(f)

def save(data):
    os.makedirs(os.path.dirname(REGISTRY), exist_ok=True)
    with open(REGISTRY, "w") as f: json.dump(data, f, indent=2)

def heartbeat(worker_id):
    data = load()
    data[worker_id] = {
        "last_seen": time.time()
    }
    save(data)
