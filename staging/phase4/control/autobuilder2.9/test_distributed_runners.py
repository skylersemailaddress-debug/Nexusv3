import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

API_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(API_ROOT))

from app.routes import jobs as jobs_module  # noqa: E402


class FakeCursor:
    def __init__(self, script):
        self.script = list(script)
        self.executed = []

    def execute(self, sql, params=None):
        self.executed.append((sql, params))
        if not self.script:
            return
        step = self.script[0]
        expected = step.get("contains")
        if expected and expected not in sql:
            raise AssertionError(f"Expected SQL containing {expected!r}, got: {sql}")

    def fetchone(self):
        if not self.script:
            return None
        step = self.script[0]
        value = step.get("fetchone")
        if step.get("advance_on_fetch", True):
            self.script.pop(0)
        return value

    def fetchall(self):
        if not self.script:
            return []
        step = self.script[0]
        value = step.get("fetchall", [])
        if step.get("advance_on_fetch", True):
            self.script.pop(0)
        return value


class FakeCursorContext:
    def __init__(self, cursor):
        self.cursor_obj = cursor

    def __enter__(self):
        return self.cursor_obj

    def __exit__(self, exc_type, exc, tb):
        return False


class FakeConn:
    def __init__(self, cursor):
        self.cursor_obj = cursor
        self.committed = False

    def cursor(self):
        return FakeCursorContext(self.cursor_obj)

    def commit(self):
        self.committed = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def _runner_row(runner_id: str, desired_state: str = "active"):
    return {"runner_id": runner_id, "desired_state": desired_state}


def test_lease_safety_prevents_double_claim():
    cursor_a = FakeCursor(
        [
            {"contains": "insert into runner_heartbeats", "fetchone": _runner_row("runner-a")},
            {"contains": "update jobs", "fetchall": []},
            {"contains": "select count(*) as active_jobs", "fetchone": {"active_jobs": 0}},
            {"contains": "for update skip locked", "fetchone": {"id": "job-1"}},
            {"contains": "update jobs", "fetchone": {"id": "job-1", "project_id": "proj-1", "capability_id": "local.powershell"}},
            {"contains": "insert into runner_heartbeats", "fetchone": _runner_row("runner-a")},
            {"contains": "update runner_heartbeats"},
        ]
    )
    cursor_b = FakeCursor(
        [
            {"contains": "insert into runner_heartbeats", "fetchone": _runner_row("runner-b")},
            {"contains": "update jobs", "fetchall": []},
            {"contains": "select count(*) as active_jobs", "fetchone": {"active_jobs": 0}},
            {"contains": "for update skip locked", "fetchone": None},
        ]
    )

    with patch.object(jobs_module, "get_conn", side_effect=[FakeConn(cursor_a), FakeConn(cursor_b)]), patch.object(
        jobs_module, "_write_job_event"
    ):
        first = jobs_module.claim_job_logic({"runner_id": "runner-a", "capabilities": ["local.powershell"], "max_concurrency": 1})
        second = jobs_module.claim_job_logic({"runner_id": "runner-b", "capabilities": ["local.powershell"], "max_concurrency": 1})

    assert first["job"]["id"] == "job-1"
    assert second["job"] is None


def test_expired_lease_recovery_requeues_and_reclaims_job():
    cursor = FakeCursor(
        [
            {"contains": "insert into runner_heartbeats", "fetchone": _runner_row("runner-a")},
            {"contains": "update jobs", "fetchall": [{"id": "job-stale"}]},
            {"contains": "select count(*) as active_jobs", "fetchone": {"active_jobs": 0}},
            {"contains": "for update skip locked", "fetchone": {"id": "job-stale"}},
            {"contains": "update jobs", "fetchone": {"id": "job-stale", "project_id": "proj-1", "capability_id": "local.powershell"}},
            {"contains": "insert into runner_heartbeats", "fetchone": _runner_row("runner-a")},
            {"contains": "update runner_heartbeats"},
        ]
    )

    with patch.object(jobs_module, "get_conn", return_value=FakeConn(cursor)), patch.object(jobs_module, "_write_job_event"):
        result = jobs_module.claim_job_logic({"runner_id": "runner-a", "capabilities": ["local.powershell"], "max_concurrency": 1})

    assert result["recovered_stale_jobs"] == 1
    assert result["job"]["id"] == "job-stale"


def test_retry_scheduling_sets_retrying_state_and_next_retry():
    claimed_job = {
        "id": "job-1",
        "project_id": "proj-1",
        "capability_id": "local.powershell",
        "status": "running",
        "claimed_by": "runner-a",
        "claim_token": "claim-1",
        "inputs": {},
        "retry_count": 0,
        "max_retries": 2,
        "lease_expires_at": datetime.now(timezone.utc).replace(year=2099),
        "started_at": datetime.now(timezone.utc),
    }
    retried_job = {
        **claimed_job,
        "status": "retrying",
        "retry_count": 1,
        "completed_at": "2026-04-08T00:00:00Z",
        "next_retry_at": "2026-04-08T00:00:30Z",
        "inputs": {"attempt_count": 1},
    }
    cursor = FakeCursor(
        [
            {"contains": "select * from jobs", "fetchone": claimed_job},
            {"contains": "update jobs", "fetchone": retried_job},
        ]
    )

    with patch.object(jobs_module, "get_conn", return_value=FakeConn(cursor)), patch.object(
        jobs_module, "_create_job_artifact", return_value={"id": "artifact-job-1"}
    ), patch.object(jobs_module, "_write_job_event"), patch.object(
        jobs_module, "maybe_start_autocode"
    ) as maybe_start_autocode:
        result = jobs_module.complete_job_logic({"job_id": "job-1", "runner_id": "runner-a", "status": "failed", "error": "boom"})

    assert result["job"]["status"] == "retrying"
    assert result["job"]["retry_count"] == 1
    assert result["job"]["next_retry_at"] == "2026-04-08T00:00:30Z"
    maybe_start_autocode.assert_not_called()


def test_multi_runner_assignment_respects_capabilities():
    cursor_a = FakeCursor(
        [
            {"contains": "insert into runner_heartbeats", "fetchone": _runner_row("runner-ps")},
            {"contains": "update jobs", "fetchall": []},
            {"contains": "select count(*) as active_jobs", "fetchone": {"active_jobs": 0}},
            {"contains": "for update skip locked", "fetchone": {"id": "job-ps"}},
            {"contains": "update jobs", "fetchone": {"id": "job-ps", "project_id": "proj-1", "capability_id": "local.powershell"}},
            {"contains": "insert into runner_heartbeats", "fetchone": _runner_row("runner-ps")},
            {"contains": "update runner_heartbeats"},
        ]
    )
    cursor_b = FakeCursor(
        [
            {"contains": "insert into runner_heartbeats", "fetchone": _runner_row("runner-py")},
            {"contains": "update jobs", "fetchall": []},
            {"contains": "select count(*) as active_jobs", "fetchone": {"active_jobs": 0}},
            {"contains": "for update skip locked", "fetchone": {"id": "job-py"}},
            {"contains": "update jobs", "fetchone": {"id": "job-py", "project_id": "proj-1", "capability_id": "python.exec"}},
            {"contains": "insert into runner_heartbeats", "fetchone": _runner_row("runner-py")},
            {"contains": "update runner_heartbeats"},
        ]
    )

    with patch.object(jobs_module, "get_conn", side_effect=[FakeConn(cursor_a), FakeConn(cursor_b)]), patch.object(
        jobs_module, "_write_job_event"
    ):
        ps_job = jobs_module.claim_job_logic({"runner_id": "runner-ps", "capabilities": ["local.powershell"], "max_concurrency": 1})
        py_job = jobs_module.claim_job_logic({"runner_id": "runner-py", "capabilities": ["python.exec"], "max_concurrency": 1})

    assert ps_job["job"]["capability_id"] == "local.powershell"
    assert py_job["job"]["capability_id"] == "python.exec"
