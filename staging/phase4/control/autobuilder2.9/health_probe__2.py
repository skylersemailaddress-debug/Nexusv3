
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


def startup(root: Path):
    checks = {
        'runtime_manifest': (root / 'runtime' / 'config' / 'runtime_manifest.json').exists(),
        'retry_policy': (root / 'runtime' / 'config' / 'retry_policy.json').exists(),
        'execution_graph': (root / 'runtime' / 'execution_graph.json').exists(),
        'build_plan': (root / 'build' / 'plans' / 'build_graph_plan.json').exists(),
    }
    status = 'ready' if all(checks.values()) else 'failed'
    return {'probe':'startup','status':status,'checked_at':now(),'checks':checks}

def readiness(root: Path):
    state = load_json(root / 'runtime' / 'state' / 'execution_state.json', default={})
    checks = {
        'results_dir': (root / 'runtime' / 'results').exists(),
        'state_dir': (root / 'runtime' / 'state').exists(),
        'not_mid_rollback': not state.get('rollback_required', False),
    }
    status = 'ready' if all(checks.values()) else 'not_ready'
    return {'probe':'readiness','status':status,'checked_at':now(),'checks':checks}

def liveness(root: Path):
    state = load_json(root / 'runtime' / 'state' / 'execution_state.json', default={})
    heartbeat = state.get('updated_at') or state.get('finished_at') or state.get('started_at')
    age_seconds = None
    alive = True
    if heartbeat:
        try:
            dt = datetime.fromisoformat(heartbeat.replace('Z', '+00:00'))
            age_seconds = (datetime.now(timezone.utc) - dt).total_seconds()
            alive = age_seconds < 86400
        except Exception:
            alive = False
    payload = {'probe':'liveness','status':'alive' if alive else 'stale','checked_at':now(),'heartbeat':heartbeat,'age_seconds':age_seconds}
    return payload

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('probe', choices=['startup','readiness','liveness'])
    parser.add_argument('--root', default=None)
    args = parser.parse_args()
    root = detect_root(args.root)
    payload = {'startup': startup, 'readiness': readiness, 'liveness': liveness}[args.probe](root)
    print(json.dumps(payload, indent=2))
    raise SystemExit(0 if payload['status'] in ('ready','alive') else 1)
