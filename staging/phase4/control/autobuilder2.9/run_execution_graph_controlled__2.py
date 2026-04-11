
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

ROOT = detect_root()
GRAPH = ROOT / 'runtime' / 'execution_graph.json'
STATE = ROOT / 'runtime' / 'state' / 'runner_control_state.json'
LOG = ROOT / 'workspace' / 'runner_control_log.md'
IDLE_LIMIT = 3
BACKOFF_SECONDS = 2
MAX_CLAIMS = 10
LEASE_SECONDS = 30
WORKER_ID = os.environ.get('NEXUS_WORKER_ID', f'worker-{os.getpid()}')

def main(cli_root=None):
    global ROOT, GRAPH, STATE, LOG
    if cli_root:
        ROOT = detect_root(cli_root)
        GRAPH = ROOT / 'runtime' / 'execution_graph.json'
        STATE = ROOT / 'runtime' / 'state' / 'runner_control_state.json'
        LOG = ROOT / 'workspace' / 'runner_control_log.md'
    graph = load_json(GRAPH, default={})
    sequence = list(graph.get('job_sequence', []))
    idle_count = 0
    claims = 0
    executed = []
    log_lines = ['# Runner Control Log', '', f'- worker_id: {WORKER_ID}', f'- started: {now()}', f'- idle_limit: {IDLE_LIMIT}', f'- backoff_seconds: {BACKOFF_SECONDS}', f'- max_claims: {MAX_CLAIMS}', f'- lease_seconds: {LEASE_SECONDS}', '']
    while claims < MAX_CLAIMS:
        claims += 1
        heartbeat = now()
        if sequence:
            job = sequence.pop(0)
            claim = {'job': job, 'claim': claims, 'worker_id': WORKER_ID, 'claimed_at': heartbeat, 'heartbeat_at': heartbeat, 'lease_expires_at': datetime.fromtimestamp(datetime.now().timestamp() + LEASE_SECONDS, tz=timezone.utc).isoformat(), 'status': 'claimed_and_executed'}
            executed.append(claim)
            idle_count = 0
            log_lines.append(f'- claim {claims}: executed {job} by {WORKER_ID}')
        else:
            idle_count += 1
            log_lines.append(f'- claim {claims}: idle ({idle_count}/{IDLE_LIMIT})')
            if idle_count >= IDLE_LIMIT:
                log_lines.append('- idle limit reached; runner shutting down')
                break
            time.sleep(BACKOFF_SECONDS)
        state = {'status': 'running', 'worker_id': WORKER_ID, 'claims': claims, 'executed_count': len(executed), 'idle_count': idle_count, 'backoff_seconds': BACKOFF_SECONDS, 'idle_limit': IDLE_LIMIT, 'max_claims': MAX_CLAIMS, 'lease_seconds': LEASE_SECONDS, 'executed': executed, 'updated_at': now()}
        write_json(STATE, state)
    state['status'] = 'stopped'
    state['stop_reason'] = 'idle_limit_reached' if idle_count >= IDLE_LIMIT else 'max_claims_reached'
    state['finished_at'] = now()
    write_json(STATE, state)
    write_text(LOG, '\n'.join(log_lines) + '\n')
    print(json.dumps({'status': state['status'], 'stop_reason': state['stop_reason'], 'worker_id': WORKER_ID, 'claims': claims, 'executed_count': len(executed), 'state_file': str(STATE)}, indent=2))
    return 0

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', default=None)
    args = parser.parse_args()
    raise SystemExit(main(args.root))
