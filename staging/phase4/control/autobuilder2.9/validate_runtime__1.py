
import argparse
import hashlib
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

FAILURES = {
    "CONFIG_ERROR",
    "GRAPH_ERROR",
    "DEPENDENCY_BLOCKED",
    "HANDLER_ERROR",
    "ARTIFACT_WRITE_ERROR",
    "STATE_RECOVERY_ERROR",
    "VALIDATION_ERROR",
    "TRANSIENT_RUNTIME_ERROR",
}

def now():
    return datetime.now(timezone.utc).isoformat()

def load_json(path: Path, default=None):
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8-sig"))
    return {} if default is None else default

def write_json(path: Path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

def write_text(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def sanitize(name: str) -> str:
    return "".join(ch if ch.isalnum() or ch in ("_", "-") else "_" for ch in name)

def detect_root(cli_root=None) -> Path:
    if cli_root:
        return Path(cli_root)
    return Path(__file__).resolve().parents[2]


def validate(root: Path):
    errors = []
    required_dirs = ["build", "builder", "runtime", "specs", "workspace", "repos"]
    for rel in required_dirs:
        if not (root / rel).exists():
            errors.append(f"missing required directory: {rel}")
    required_files = [
        root / "runtime" / "execution_graph.json",
        root / "build" / "plans" / "build_graph_plan.json",
        root / "runtime" / "config" / "runtime_manifest.json",
        root / "runtime" / "config" / "retry_policy.json",
    ]
    for path in required_files:
        if not path.exists():
            errors.append(f"missing required file: {path.relative_to(root)}")
    graph = load_json(root / "runtime" / "execution_graph.json", default={})
    if not graph.get("job_sequence"):
        errors.append("execution graph missing job_sequence")
    plan = load_json(root / "build" / "plans" / "build_graph_plan.json", default={})
    if not plan.get("nodes"):
        errors.append("build graph plan missing nodes")
    node_jobs = {n.get("job") for n in plan.get("nodes", []) if n.get("job")}
    for job in graph.get("job_sequence", []):
        if job not in node_jobs:
            errors.append(f"graph job has no node binding: {job}")
    result = {
        "status": "ok" if not errors else "failed",
        "checked_at": now(),
        "root": str(root),
        "errors": errors,
    }
    print(json.dumps(result, indent=2))
    return 0 if not errors else 1

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=None)
    args = parser.parse_args()
    raise SystemExit(validate(detect_root(args.root)))
