from __future__ import annotations

import difflib
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

from psycopg.types.json import Json

from app.db import get_conn
from app.services.repo_service import repo_read, repo_write


APPROVAL_MODES = {"suggest_only", "manual", "auto_read", "auto_safe_write", "auto_write"}
ALLOWED_WRITE_ROOTS = ("apps/api/app/", "apps/api/tests/", "scripts/")
BLOCKED_PREFIXES = (".git/", "state/", "sql/migrations/", "secrets/", ".env")


def _normalize_rel_path(path: str) -> str:
    return str(PurePosixPath(str(path).replace("\\", "/").lstrip("/")))


def _is_allowed_write_path(path: str) -> tuple[bool, str]:
    normalized = _normalize_rel_path(path)
    if normalized.startswith(BLOCKED_PREFIXES):
        return False, f"blocked path: {normalized}"
    if not any(normalized.startswith(root) for root in ALLOWED_WRITE_ROOTS):
        return False, f"path outside allowed roots: {normalized}"
    return True, normalized


def _enqueue_job(job_id: str, project_id: str, capability_id: str, command: str, approval_mode: str, risk_level: str, requested_by: str | None = None, extra_inputs: dict | None = None) -> dict:
    inputs = {"command": command}
    if extra_inputs:
        inputs.update(extra_inputs)
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
            (job_id, project_id, capability_id, approval_mode, risk_level, Json(inputs), requested_by),
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


def _fetch_artifact(artifact_id: str) -> dict | None:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            select id, project_id, kind, title, payload, meta, created_at, updated_at
            from artifacts where id = %s
            """,
            (artifact_id,),
        )
        return cur.fetchone()


def _find_latest_validation_for_packet(project_id: str, packet_artifact_id: str) -> dict | None:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            select id, project_id, kind, title, payload, meta, created_at, updated_at
            from artifacts
            where project_id = %s
              and kind = 'generated_code_validation_result'
              and coalesce((payload->>'artifact_id'), '') = %s
            order by created_at desc
            limit 1
            """,
            (project_id, packet_artifact_id),
        )
        return cur.fetchone()


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
    task_text = (task or "").strip()
    replace_match = re.match(r"^replace:\s*(.*?)\s*=>\s*(.*?)\s*$", task_text, re.IGNORECASE)
    if replace_match:
        old_text = replace_match.group(1)
        new_text = replace_match.group(2)
        return original_content.replace(old_text, new_text)

    note = _make_change_note(task, acceptance_criteria)
    if suffix in {".py", ".md", ".txt", ".json", ".yaml", ".yml", ".toml", ".ini", ".sql", ".ps1", ".sh"}:
        if "SKYLEROS_AUTOGEN_NOTE_START" in original_content:
            return original_content
        return original_content.rstrip() + note
    return original_content


def generate_code_packet(
    project_id: str,
    task: str,
    target_paths: list[str] | None = None,
    acceptance_criteria: list[str] | None = None,
    approval_mode: str = "suggest_only",
    source_job_id: str | None = None,
    chain_id: str | None = None,
    failure_signature: str | None = None,
    validation_command: str | None = None,
) -> dict:
    target_paths = target_paths or []
    acceptance_criteria = acceptance_criteria or []
    if approval_mode not in APPROVAL_MODES:
        approval_mode = "suggest_only"
    draft_files: list[dict] = []
    errors: list[dict] = []
    for rel_path in target_paths:
        rel_path = _normalize_rel_path(rel_path)
        allowed, reason = _is_allowed_write_path(rel_path)
        if not allowed:
            errors.append({"path": rel_path, "error": reason})
            continue
        read_result = repo_read(rel_path)
        if not read_result.get("ok"):
            errors.append({"path": rel_path, "error": read_result.get("error", "Unable to read path")})
            continue
        if read_result.get("kind") != "file":
            errors.append({"path": rel_path, "error": "Target path is not a file"})
            continue

        original_content = read_result.get("content", "")
        proposed_content = _draft_for_file(rel_path, original_content, task, acceptance_criteria)
        task_text = (task or "").strip()
        operations: list[dict] = []
        replace_match = re.match(r"^replace:\s*(.*?)\s*=>\s*(.*?)\s*$", task_text, re.IGNORECASE)
        if replace_match:
            old_text = replace_match.group(1)
            new_text = replace_match.group(2)
            applied = old_text in original_content
            operations.append({
                "type": "replace_text",
                "from": old_text,
                "to": new_text,
                "applied": applied,
            })
        else:
            operations.append({
                "type": "draft_update",
                "applied": original_content != proposed_content,
            })

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
            "operations": operations,
            "changed": original_content != proposed_content,
        })

    derived_validation_command = validation_command
    if not derived_validation_command:
        python_targets = [p for p in target_paths if str(p).endswith(".py")]
        if python_targets and len(python_targets) == len(target_paths):
            derived_validation_command = "python -m py_compile " + " ".join(target_paths)
        else:
            derived_validation_command = "structural"

    payload = {
        "ok": len(errors) == 0,
        "project_id": project_id,
        "task": task,
        "target_paths": target_paths,
        "acceptance_criteria": acceptance_criteria,
        "plan": [
            "Inspect relevant files",
            "Draft concrete file changes",
            "Validate structural safety before apply",
            "Apply approved patch set",
            "Retry original job after apply",
        ],
        "draft_files": draft_files,
        "generated_patch_spec": [{"path": item["path"], "intent": item["intent"], "changed": item["changed"]} for item in draft_files],
        "approval_mode": approval_mode,
        "errors": errors,
        "generation_mode": "bounded_patch_packet_v2",
        "source_job_id": source_job_id,
        "chain_id": chain_id,
        "failure_signature": failure_signature,
        "validation": {
            "command": derived_validation_command,
            "mode": "structural_first",
            "expected": "safe_packet",
        },
    }
    artifact = _create_artifact(project_id, "generated_code_packet", f"Generated Code Packet {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%SZ')}", payload, {"source": "dev_generate_code", "chain_id": chain_id, "source_job_id": source_job_id})
    payload["artifact_id"] = artifact["id"]
    return payload


def validate_generated_code(project_id: str, artifact_id: str, command: str | None = None, requested_by: str | None = None, approval_mode: str = "auto_read") -> dict:
    artifact = _fetch_artifact(artifact_id)
    if not artifact:
        return {"ok": False, "error": f"Artifact not found: {artifact_id}"}
    if artifact.get("project_id") != project_id:
        return {"ok": False, "error": f"Artifact {artifact_id} does not belong to project {project_id}"}
    if artifact.get("kind") not in {"generated_code_packet", "dev_code_packet"}:
        return {"ok": False, "error": f"Artifact {artifact_id} is not a generated code packet"}

    payload = artifact.get("payload") or {}
    drafts = payload.get("draft_files") or []
    checks: list[dict] = []
    blocked: list[str] = []
    changed_count = 0

    for draft in drafts:
        path = _normalize_rel_path(draft.get("path") or "")
        allowed, reason = _is_allowed_write_path(path)
        changed = bool(draft.get("changed"))
        proposed = draft.get("proposed_content")
        if changed:
            changed_count += 1
        if not allowed:
            blocked.append(path)
        checks.append({
            "path": path,
            "allowed": allowed,
            "reason": reason,
            "changed": changed,
            "has_proposed_content": proposed is not None,
            "has_diff": bool(draft.get("diff_preview")),
        })

    passed = bool(drafts) and changed_count > 0 and not blocked and all(c["has_proposed_content"] for c in checks)
    validation_payload = {
        "ok": passed,
        "project_id": project_id,
        "artifact_id": artifact_id,
        "requested_by": requested_by,
        "approval_mode": approval_mode,
        "command": command or (payload.get("validation") or {}).get("command") or "structural",
        "mode": "structural",
        "changed_count": changed_count,
        "blocked_paths": blocked,
        "checks": checks,
        "status": "passed" if passed else "failed",
    }
    validation_artifact = _create_artifact(project_id, "generated_code_validation_result", f"Generated Code Validation {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%SZ')}", validation_payload, {"source": "dev_validate_generated_code", "artifact_id": artifact_id})
    return {"ok": passed, "validation": validation_payload, "artifact": validation_artifact}


def apply_generated_code(project_id: str, artifact_id: str, requested_by: str | None = None, approval_mode: str = "manual", create_backup: bool = True) -> dict:
    if approval_mode not in APPROVAL_MODES:
        approval_mode = "manual"
    artifact = _fetch_artifact(artifact_id)
    if not artifact:
        return {"ok": False, "error": f"Artifact not found: {artifact_id}"}
    if artifact.get("project_id") != project_id:
        return {"ok": False, "error": f"Artifact {artifact_id} does not belong to project {project_id}"}
    if artifact.get("kind") not in {"generated_code_packet", "dev_code_packet"}:
        return {"ok": False, "error": f"Artifact {artifact_id} is not a generated code packet"}

    latest_validation = _find_latest_validation_for_packet(project_id, artifact_id)
    validation_payload = (latest_validation or {}).get("payload") or {}
    if not latest_validation or not validation_payload.get("ok"):
        return {"ok": False, "error": f"Artifact {artifact_id} has no passing validation result"}

    payload = artifact.get("payload") or {}
    drafts = payload.get("draft_files") or []
    applied = []
    backups = []
    for draft in drafts:
        rel_path = _normalize_rel_path(draft.get("path") or "")
        allowed, reason = _is_allowed_write_path(rel_path)
        if not allowed:
            return {"ok": False, "error": reason}
        proposed = draft.get("proposed_content")
        if proposed is None or not draft.get("changed"):
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
        "validation_artifact_id": latest_validation["id"],
        "applied": applied,
        "backups": backups,
        "requested_by": requested_by,
        "approval_mode": approval_mode,
    }
    apply_artifact = _create_artifact(project_id, "generated_code_apply_result", f"Generated Code Apply Result {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%SZ')}", apply_payload, {"source": "dev_apply_generated_code"})
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
    inputs = dict(job.get("inputs") or {})
    command = inputs.get("command")
    if not command:
        return {"ok": False, "error": f"Job {job_id} has no retryable command"}
    autocode = dict(inputs.get("autocode") or {})
    if autocode:
        autocode["retry_of_job_id"] = job_id
        autocode["state"] = "retrying_original"
    extra_inputs = {k: v for k, v in inputs.items() if k != "command"}
    if autocode:
        extra_inputs["autocode"] = autocode
    new_job_id = f"{job_id}_retry"
    new_job = _enqueue_job(new_job_id, job.get("project_id"), job.get("capability_id"), command, job.get("approval_mode") or "auto_read", job.get("risk_level") or "low", requested_by, extra_inputs=extra_inputs)
    return {"ok": True, "job": new_job, "retried_from": job_id}


def enqueue_generated_validation(project_id: str, artifact_id: str, command: str, requested_by: str | None = None, approval_mode: str = "auto_read") -> dict:
    if not command or command == "structural":
        return validate_generated_code(project_id, artifact_id, command="structural", requested_by=requested_by, approval_mode=approval_mode)
    job_id = f"job_validate_{uuid.uuid4().hex[:8]}"
    response = enqueue_script_job(project_id, command, requested_by, job_id=job_id, approval_mode=approval_mode, risk_level="low")
    if response.get("ok"):
        _create_artifact(project_id, "dev_validation_request", f"Validation Request {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%SZ')}", {
            "artifact_id": artifact_id,
            "job_id": response["job"]["id"],
            "command": command,
        }, {"source": "dev_validate_generated_code"})
    return response



