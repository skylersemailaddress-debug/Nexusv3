import json, time, uuid, os

QUEUE = "runtime/queue/lease_queue.json"
STATE = "runtime/state/runner_state.json"

def load(path):
    if not os.path.exists(path): return {}
    with open(path) as f: return json.load(f)

def save(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f: json.dump(data, f, indent=2)

def claim_job(worker_id):
    q = load(QUEUE)
    for job in q.get("jobs", []):
        if job.get("status") == "pending":
            job["status"] = "claimed"
            job["worker"] = worker_id
            job["claimed_at"] = time.time()
            save(QUEUE, q)
            return job
    return None

def run():
    worker_id = str(uuid.uuid4())
    while True:
        job = claim_job(worker_id)
        if not job:
            time.sleep(2)
            continue
        print(f"Running job {job['id']} on {worker_id}")
        time.sleep(1)
        job["status"] = "done"
        q = load(QUEUE)
        for j in q["jobs"]:
            if j["id"] == job["id"]:
                j.update(job)
        save(QUEUE, q)

if __name__ == "__main__":
    run()
