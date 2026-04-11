
from __future__ import annotations

import difflib
import uuid
from datetime import datetime, timezone
from pathlib import Path

from psycopg.types.json import Json

from app.db import get_conn
from app.services.repo_service import repo_apply_patch, repo_read, repo_write, _safe_path, REPO_ROOT


APPROVAL_MODES = {"suggest_only", "manual", "auto_read", "auto_safe_write"}


def _enqueue_job(job_id: str, project_id: str, capability_id: str, command: str, approval_mode: str, risk_level: str, requested_by: str | None = None) -> dict:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            insert into jobs (id, project_id, capability_id, status, approval_mode, risk_level, inputs, requested_by)
            values (%s, %s, %s, 'queued', %s, %s, %s, %s)
            on conflict (id) do update set
                project_id = excluded.project_id,
                capability_id = excluded.capability_id,
                status = 'queued',
                approval_mode = excluded.approval_mode,
                risk_level = excluded.risk_level,
                inputs = excluded.inputs,
                requested_by = excluded.requested_by,
                error = null,
                result = null,
                started_at = null,
                completed_at = null,
                updated_at = now()
            returning id, project_id, capability_id, status, approval_mode, risk_level, inputs, requested_by, created_at, updated_at
            """,
            (job_id, project_id, capability_id, approval_mode, risk_level, Json({"command": command}), requested_by),
        )
        row = cur.fetchone()
        conn.commit()
        return row


def _create_artifact(project_id: str, kind: str, title: str, payload: dict, meta: dict | None = None) -> dict:
    artifact_id = f"{kind}_{uuid.uuid4().hex[:16]}"
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            insert into artifacts (id, project_id, kind, title, path, payload, meta)
            values (%s, %s, %s, %s, null, %s, %s)
            returning id, project_id, kind, title, path, payload, meta, created_at, updated_at
            """,
            (artifact_id, project_id, kind, title, Json(payload), Json(meta or {})),
        )
        row = cur.fetchone()
        conn.commit()
    return row


def enqueue_script_job(project_id: str, command: str, requested_by: str | None = None, job_id: str | None = None, approval_mode: str = "auto_read", risk_level: str = "medium") -> dict:
    job_id = job_id or f"job_script_{abs(hash((project_id, command))) % 1000000000}"
    return {"ok": True, "job": _enqueue_job(job_id, project_id, "local.powershell", command, approval_mode, risk_level, requested_by)}


def enqueue_test_job(project_id: str, command: str = "pytest -q", requested_by: str | None = None, job_id: str | None = None, approval_mode: str = "auto_read") -> dict:
    job_id = job_id or f"job_test_{abs(hash((project_id, command))) % 1000000000}"
    return {"ok": True, "job": _enqueue_job(job_id, project_id, "local.powershell", command, approval_mode, "medium", requested_by)}


def enqueue_lint_job(project_id: str, command: str = "python -m compileall apps", requested_by: str | None = None, job_id: str | None = None, approval_mode: str = "auto_read") -> dict:
    job_id = job_id or f"job_lint_{abs(hash((project_id, command))) % 1000000000}"
    return {"ok": True, "job": _enqueue_job(job_id, project_id, "local.powershell", command, approval_mode, "low", requested_by)}


def _make_change_note(task: str, acceptance_criteria: list[str]) -> str:
    lines = ["", "# SKYLEROS_AUTOGEN_NOTE_START", f"# Task: {task.strip()}"]
    for criterion in acceptance_criteria[:5]:
        lines.append(f"# Acceptance: {criterion}")
    lines.append(f"# Generated: {datetime.now(timezone.utc).isoformat()}")
    lines.append("# SKYLEROS_AUTOGEN_NOTE_END")
    return "\n".join(lines) + "\n"


def _draft_for_file(path: str, original_content: str, task: str, acceptance_criteria: list[str]) -> str:
    suffix = Path(path).suffix.lower()
    if suffix == ".py":
        note = _make_change_note(task, acceptance_criteria)
        if "SKYLEROS_AUTOGEN_NOTE_START" in original_content:
            return original_content
        return original_content.rstrip() + note
    if suffix in {".md", ".txt", ".json", ".yaml", ".yml", ".toml", ".ini", ".sql", ".ps1", ".sh"}:
        note = _make_change_note(task, acceptance_criteria)
        if "SKYLEROS_AUTOGEN_NOTE_START" in original_content:
            return original_content
        return original_content.rstrip() + note
    return original_content


def generate_code_packet(project_id: str, task: str, target_paths: list[str] | None = None, acceptance_criteria: list[str] | None = None, approval_mode: str = "suggest_only") -> dict:
    target_paths = target_paths or []
    acceptance_criteria = acceptance_criteria or []
    if approval_mode not in APPROVAL_MODES:
        approval_mode = "suggest_only"
    draft_files: list[dict] = []
    errors: list[dict] = []
    for rel_path in target_paths:
        read_result = repo_read(rel_path)
        if not read_result.get("ok"):
            errors.append({"path": rel_path, "error": read_result.get("error", "Unable to read path")})
            continue
        if read_result.get("kind") != "file":
            errors.append({"path": rel_path, "error": "Target path is not a file"})
            continue
        original_content = read_result.get("content", "")
        proposed_content = _draft_for_file(rel_path, original_content, task, acceptance_criteria)
        diff_preview = list(
            difflib.unified_diff(
                original_content.splitlines(),
                proposed_content.splitlines(),
                fromfile=f"a/{rel_path}",
                tofile=f"b/{rel_path}",
                lineterm="",
            )
        )[:200]
        draft_files.append({
            "path": rel_path,
            "intent": f"Update {rel_path} to satisfy task",
            "original_content": original_content,
            "proposed_content": proposed_content,
            "diff_preview": diff_preview,
            "changed": original_content != proposed_content,
        })
    payload = {
        "ok": True,
        "project_id": project_id,
        "task": task,
        "target_paths": target_paths,
        "acceptance_criteria": acceptance_criteria,
        "plan": [
            "Inspect relevant files",
            "Draft concrete file changes",
            "Apply approved patch set",
            "Run validation command",
            "Evaluate result and retry if needed",
        ],
        "draft_files": draft_files,
        "generated_patch_spec": [{"path": item["path"], "intent": item["intent"], "changed": item["changed"]} for item in draft_files],
        "approval_mode": approval_mode,
        "errors": errors,
        "generation_mode": "template_backed_patch_draft",
    }
    artifact = _create_artifact(project_id, "dev_code_packet", f"Dev Code Packet {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%SZ')}", payload, {"source": "dev_generate_code"})
    payload["artifact_id"] = artifact["id"]
    return payload


def apply_generated_code(project_id: str, artifact_id: str, requested_by: str | None = None, approval_mode: str = "manual", create_backup: bool = True) -> dict:
    if approval_mode not in APPROVAL_MODES:
        approval_mode = "manual"
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            select id, project_id, kind, title, payload, meta, created_at, updated_at
            from artifacts where id = %s
            """,
            (artifact_id,),
        )
        artifact = cur.fetchone()
    if not artifact:
        return {"ok": False, "error": f"Artifact not found: {artifact_id}"}
    if artifact.get("project_id") != project_id:
        return {"ok": False, "error": f"Artifact {artifact_id} does not belong to project {project_id}"}
    if artifact.get("kind") != "dev_code_packet":
        return {"ok": False, "error": f"Artifact {artifact_id} is not a dev code packet"}
    payload = artifact.get("payload") or {}
    drafts = payload.get("draft_files") or []
    applied = []
    backups = []
    for draft in drafts:
        rel_path = draft.get("path")
        proposed = draft.get("proposed_content")
        if not rel_path or proposed is None:
            continue
        read_result = repo_read(rel_path)
        if not read_result.get("ok"):
            return {"ok": False, "error": read_result.get("error", f"Unable to read {rel_path}")}
        original = read_result.get("content", "")
        if create_backup:
            backup_path = f".skyler_backups/{Path(rel_path).name}.{uuid.uuid4().hex[:8]}.bak"
            repo_write(backup_path, original, True)
            backups.append({"original_path": rel_path, "backup_path": backup_path})
        write_result = repo_write(rel_path, proposed, True)
        if not write_result.get("ok"):
            return write_result
        applied.append({"path": rel_path, "diff_preview": write_result.get("diff_preview", []), "bytes_written": write_result.get("bytes_written", 0)})
    apply_payload = {
        "ok": True,
        "artifact_id": artifact_id,
        "project_id": project_id,
        "applied": applied,
        "backups": backups,
        "requested_by": requested_by,
        "approval_mode": approval_mode,
    }
    apply_artifact = _create_artifact(project_id, "dev_apply_result", f"Dev Apply Result {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%SZ')}", apply_payload, {"source": "dev_apply_generated_code"})
    apply_payload["apply_artifact_id"] = apply_artifact["id"]
    return apply_payload


def evaluate_job_result(job_id: str) -> dict:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("""
            select id, capability_id, status, approval_mode, risk_level, result, error, created_at, updated_at
            from jobs where id = %s
        """, (job_id,))
        job = cur.fetchone()
    if not job:
        return {"ok": False, "error": f"Job not found: {job_id}"}
    result = job.get("result") or {}
    stdout = (result.get("stdout") or "").strip()
    stderr = (result.get("stderr") or "").strip()
    return {
        "ok": True,
        "job": job,
        "evaluation": {
            "status": job.get("status"),
            "succeeded": job.get("status") == "completed",
            "summary": stdout[:400] if stdout else stderr[:400] if stderr else "No output available.",
            "needs_retry": job.get("status") != "completed",
        },
    }


def retry_job_step(job_id: str, requested_by: str | None = None) -> dict:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("select id, project_id, capability_id, inputs, approval_mode, risk_level from jobs where id = %s", (job_id,))
        job = cur.fetchone()
    if not job:
        return {"ok": False, "error": f"Job not found: {job_id}"}
    command = (job.get("inputs") or {}).get("command")
    if not command:
        return {"ok": False, "error": f"Job {job_id} has no retryable command"}
    new_job_id = f"{job_id}_retry"
    new_job = _enqueue_job(new_job_id, job.get("project_id"), job.get("capability_id"), command, job.get("approval_mode") or "auto_read", job.get("risk_level") or "low", requested_by)
    return {"ok": True, "job": new_job, "retried_from": job_id}


def enqueue_generated_validation(project_id: str, artifact_id: str, command: str, requested_by: str | None = None, approval_mode: str = "auto_read") -> dict:
    job_id = f"job_validate_{uuid.uuid4().hex[:8]}"
    response = enqueue_script_job(project_id, command, requested_by, job_id=job_id, approval_mode=approval_mode, risk_level="low")
    if response.get("ok"):
        _create_artifact(project_id, "dev_validation_request", f"Validation Request {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%SZ')}", {
            "artifact_id": artifact_id,
            "job_id": response["job"]["id"],
            "command": command,
        }, {"source": "dev_validate_generated_code"})
    return response
