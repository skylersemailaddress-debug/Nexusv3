import json

QUEUE = "runtime/queue/lease_queue.json"

def pause_all():
    q = json.load(open(QUEUE))
    for j in q["jobs"]:
        j["paused"] = True
    json.dump(q, open(QUEUE, "w"), indent=2)

def resume_all():
    q = json.load(open(QUEUE))
    for j in q["jobs"]:
        j.pop("paused", None)
    json.dump(q, open(QUEUE, "w"), indent=2)
