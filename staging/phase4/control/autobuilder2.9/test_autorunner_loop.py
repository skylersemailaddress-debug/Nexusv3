import sys
from pathlib import Path
from unittest.mock import patch

API_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(API_ROOT))

from automation_loop import NexusAutorunner, ProjectSnapshot  # noqa: E402


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload
        self.content = b"{}"

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []
        self.headers = {}

    def request(self, method, url, json=None, timeout=None):
        self.calls.append({"method": method, "url": url, "json": json, "timeout": timeout})
        if not self.responses:
            raise AssertionError(f"Unexpected request: {method} {url}")
        return FakeResponse(self.responses.pop(0))


def _snapshot(
    objective="",
    next_step="",
    status="active",
    jobs=None,
    artifacts=None,
    recent_messages=None,
    next_action_kind="execution",
):
    return ProjectSnapshot(
        now={"ok": True, "project_id": "proj-1"},
        build_context={"ok": True, "project_id": "proj-1"},
        resume={
            "ok": True,
            "project_id": "proj-1",
            "objective": objective,
            "next_step": next_step,
            "recent_messages": recent_messages or [],
            "context": {
                "project_state": {
                    "status": status,
                    "structured_state": {"meta": {"next_action_kind": next_action_kind}},
                }
            },
        },
        jobs=jobs or [],
        artifacts=artifacts or [],
    )


def test_fetch_snapshot_calls_now_build_context_resume_jobs_and_artifacts():
    session = FakeSession(
        [
            {"ok": True, "project_id": "proj-1"},
            {"ok": True, "project_id": "proj-1"},
            {"ok": True, "project_id": "proj-1", "context": {"project_state": {"status": "active"}}},
            {"ok": True, "items": []},
            {"ok": True, "items": []},
        ]
    )
    runner = NexusAutorunner(project_id="proj-1", session=session)

    snapshot = runner.fetch_snapshot("hello")

    assert snapshot.now["project_id"] == "proj-1"
    assert len(session.calls) == 5
    assert session.calls[0]["url"].endswith("/projects/proj-1/now")
    assert session.calls[1]["url"].endswith("/state/build-context")
    assert session.calls[2]["url"].endswith("/projects/proj-1/resume")
    assert "/system/jobs/recent" in session.calls[3]["url"]
    assert "/artifacts/list" in session.calls[4]["url"]


def test_decide_next_action_approves_pending_jobs_when_enabled():
    runner = NexusAutorunner(project_id="proj-1", auto_approve=True)
    snapshot = _snapshot(
        objective="Advance project",
        next_step="Approval required",
        jobs=[{"id": "job-1", "status": "awaiting_approval", "approval_status": "pending"}],
        recent_messages=[{"role": "user", "content": "hello"}],
    )

    decision = runner.decide_next_action(snapshot)

    assert decision["kind"] == "approve"
    assert decision["job_id"] == "job-1"


def test_run_uses_orchestrate_then_automation_until_resolved():
    runner = NexusAutorunner(project_id="proj-1", interval_seconds=0, max_cycles=5)
    snapshots = [
        _snapshot(objective="", next_step="", jobs=[], artifacts=[], recent_messages=[{"role": "user", "content": "seed"}]),
        _snapshot(
            objective="Advance project",
            next_step="Run the initial execution step",
            jobs=[],
            artifacts=[],
            recent_messages=[{"role": "user", "content": "seed"}],
            next_action_kind="execution",
        ),
        _snapshot(
            objective="Advance project",
            next_step="Persist the latest execution result to the mock Google Drive connector",
            jobs=[],
            artifacts=[{"id": "artifact-1", "kind": "execution_result"}],
            recent_messages=[{"role": "user", "content": "seed"}],
            next_action_kind="connector_sync",
        ),
        _snapshot(
            objective="Advance project",
            next_step="Review resolved objective and accumulated progress",
            status="resolved",
            jobs=[{"id": "job-1", "status": "completed"}],
            artifacts=[
                {"id": "artifact-1", "kind": "execution_result"},
                {"id": "artifact-2", "kind": "connector_sync"},
                {"id": "artifact-3", "kind": "ramble_capture"},
            ],
            recent_messages=[{"role": "user", "content": "seed"}],
            next_action_kind="review",
        ),
    ]

    with patch.object(runner, "set_ramble_mode", return_value={"ok": True}), patch.object(
        runner, "fetch_snapshot", side_effect=snapshots
    ), patch.object(runner, "append_message", return_value={"ok": True}) as append_message, patch.object(
        runner, "orchestrate", return_value={"ok": True}
    ) as orchestrate, patch.object(
        runner, "automation_tick", return_value={"ok": True}
    ) as automation_tick, patch(
        "automation_loop.time.sleep", return_value=None
    ):
        summary = runner.run()

    assert summary.resolved is True
    assert summary.objective_history == ["Advance project"]
    assert summary.next_step_history == [
        "Run the initial execution step",
        "Persist the latest execution result to the mock Google Drive connector",
        "Review resolved objective and accumulated progress",
    ]
    orchestrate.assert_called_once()
    automation_tick.assert_called_once()
    assert append_message.call_count >= 1
