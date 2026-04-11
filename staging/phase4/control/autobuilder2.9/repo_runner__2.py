from __future__ import annotations

import difflib
import json
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path, PurePosixPath

from app.services.failure_classifier import classify_failure
from app.services.repo_autoprogram import build_autoprogram_packet
from app.services.repo_service import REPO_ROOT


TEXT_EXTENSIONS = {
    '.py', '.ps1', '.json', '.md', '.txt', '.yaml', '.yml',
    '.toml', '.ini', '.sql', '.js', '.ts', '.tsx', '.jsx',
    '.html', '.css', '.sh', '.bat'
}


def _norm(path: str | None) -> str:
    return str(PurePosixPath(str(path or '').replace('\\', '/').lstrip('/')))


def _ensure_list(value) -> list:
    if isinstance(value, list):
        return value
    return []


def _allowed_path(path: str, allowed_paths: list[str], blocked_paths: list[str]) -> tuple[bool, str | None]:
    normalized = _norm(path)
    for blocked in blocked_paths:
        blocked_norm = _norm(blocked)
        if normalized == blocked_norm or normalized.startswith(blocked_norm.rstrip('/') + '/'):
            return False, f'blocked path: {normalized}'
    if not allowed_paths:
        return False, 'no allowed paths declared'
    for allowed in allowed_paths:
        allowed_norm = _norm(allowed).rstrip('/')
        if normalized == allowed_norm or normalized.startswith(allowed_norm + '/'):
            return True, None
    return False, f'path outside allowed scope: {normalized}'


def _copy_target_to_sandbox(target_root: str) -> tuple[Path, Path]:
    source_root = (REPO_ROOT / _norm(target_root)).resolve()
    try:
        source_root.relative_to(REPO_ROOT)
    except ValueError as exc:
        raise ValueError(f'target_root escapes repo root: {target_root}') from exc
    if not source_root.exists() or not source_root.is_dir():
        raise ValueError(f'target_root not found: {target_root}')
    temp_root = Path(tempfile.mkdtemp(prefix='odp_autoprogram_'))
    sandbox_root = temp_root / 'sandbox'
    shutil.copytree(source_root, sandbox_root)
    return temp_root, sandbox_root


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding='utf-8')


def _run_validation_command(command: str, cwd: Path) -> dict:
    completed = subprocess.run(
        command,
        cwd=str(cwd),
        shell=True,
        text=True,
        capture_output=True,
    )
    return {
        'ok': completed.returncode == 0,
        'command': command,
        'exit_code': completed.returncode,
        'stdout': completed.stdout,
        'stderr': completed.stderr,
    }


def _default_generate_candidate(packet: dict, attempt: int) -> dict:
    return {
        'ok': False,
        'error': 'no_generator_available',
        'reason': 'attach proposed_changes or replace generate_candidate in runtime integration',
        'attempt': attempt,
        'changes': [],
    }


# injection point for tests / future AI integration
GENERATE_CANDIDATE = _default_generate_candidate


def _build_file_diff(original: str, updated: str, rel_path: str) -> list[str]:
    return list(
        difflib.unified_diff(
            original.splitlines(),
            updated.splitlines(),
            fromfile=f'a/{rel_path}',
            tofile=f'b/{rel_path}',
            lineterm='',
        )
    )


def _apply_candidate_changes(candidate: dict, sandbox_root: Path, packet: dict) -> dict:
    scope = packet.get('edit_scope') or {}
    allowed_paths = _ensure_list(scope.get('allowed_paths'))
    blocked_paths = _ensure_list(scope.get('blocked_paths'))
    changed_files: list[dict] = []
    violations: list[str] = []

    for change in _ensure_list(candidate.get('changes')):
        rel_path = _norm(change.get('path'))
        ok, reason = _allowed_path(rel_path, allowed_paths, blocked_paths)
        if not ok:
            violations.append(reason or f'scope violation: {rel_path}')
            continue
        file_path = sandbox_root / rel_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        original = file_path.read_text(encoding='utf-8', errors='replace') if file_path.exists() else ''

        if 'content' in change:
            updated = str(change.get('content') or '')
        elif 'search' in change and 'replace' in change:
            search = str(change.get('search') or '')
            replace = str(change.get('replace') or '')
            if search not in original:
                violations.append(f'search text not found: {rel_path}')
                continue
            updated = original.replace(search, replace)
        else:
            violations.append(f'unsupported change shape: {rel_path}')
            continue

        file_path.write_text(updated, encoding='utf-8')
        changed_files.append({
            'path': rel_path,
            'diff': _build_file_diff(original, updated, rel_path),
            'changed': original != updated,
        })

    return {
        'ok': not violations and bool(changed_files),
        'changed_files': changed_files,
        'violations': violations,
    }


def _classify_validation(command: str, validation_result: dict) -> dict:
    fake_job = {
        'capability_id': 'local.powershell',
        'inputs': {'command': command},
    }
    return classify_failure(fake_job, validation_result, None)


def _artifact_root(run_id: str) -> Path:
    return REPO_ROOT / 'state' / 'autoprogram_runs' / run_id


def run_autoprogram(project_id: str, target_root: str, task: str, approval_mode: str = 'suggest_only', max_attempts: int = 3, packet: dict | None = None) -> dict:
    packet = packet or build_autoprogram_packet(
        project_id=project_id,
        target_root=target_root,
        task=task,
        approval_mode=approval_mode,
        max_attempts=max_attempts,
    )
    run_id = f'autoprogram_run_{uuid.uuid4().hex[:10]}'
    artifact_root = _artifact_root(run_id)
    artifact_root.mkdir(parents=True, exist_ok=True)

    _write_json(artifact_root / 'packet.json', packet)

    if not packet.get('ready_for_autoprogram'):
        result = {
            'ok': False,
            'run_id': run_id,
            'status': 'blocked',
            'reason': 'repo_not_ready',
            'packet': packet,
            'artifacts_path': str(artifact_root.relative_to(REPO_ROOT)).replace('\\', '/'),
        }
        _write_json(artifact_root / 'result.json', result)
        return result

    validation_command = (packet.get('requests') or {}).get('validate_generated_code', {}).get('command') or 'structural'
    execution_budget = packet.get('execution_budget') or {}
    attempts_allowed = max(1, int(execution_budget.get('max_attempts', max_attempts)))

    attempts: list[dict] = []
    final_status = 'budget_exhausted'
    final_reason = 'attempt_budget_exhausted'

    for attempt in range(1, attempts_allowed + 1):
        attempt_root = artifact_root / f'attempt_{attempt}'
        attempt_root.mkdir(parents=True, exist_ok=True)
        temp_root = None

        try:
            temp_root, sandbox_root = _copy_target_to_sandbox(target_root)
            candidate = GENERATE_CANDIDATE(packet, attempt)
            _write_json(attempt_root / 'candidate.json', candidate)

            if not candidate.get('ok'):
                attempt_result = {
                    'attempt': attempt,
                    'status': 'generation_failed',
                    'retryable': False,
                    'reason': candidate.get('reason') or candidate.get('error') or 'candidate generation failed',
                }
                _write_json(attempt_root / 'result.json', attempt_result)
                attempts.append(attempt_result)
                final_status = 'failed'
                final_reason = attempt_result['reason']
                break

            apply_result = _apply_candidate_changes(candidate, sandbox_root, packet)
            _write_json(attempt_root / 'apply.json', apply_result)

            if not apply_result.get('ok'):
                attempt_result = {
                    'attempt': attempt,
                    'status': 'scope_blocked',
                    'retryable': False,
                    'reason': '; '.join(apply_result.get('violations') or ['candidate apply failed']),
                }
                _write_json(attempt_root / 'result.json', attempt_result)
                attempts.append(attempt_result)
                final_status = 'failed'
                final_reason = attempt_result['reason']
                break

            validation_result = _run_validation_command(validation_command, sandbox_root)
            _write_json(attempt_root / 'validation.json', validation_result)

            if validation_result.get('ok'):
                attempt_result = {
                    'attempt': attempt,
                    'status': 'passed',
                    'retryable': False,
                    'changed_files': [item['path'] for item in apply_result.get('changed_files') or []],
                }
                _write_json(attempt_root / 'result.json', attempt_result)
                attempts.append(attempt_result)
                final_status = 'passed'
                final_reason = 'validation_passed'
                break

            classification = _classify_validation(validation_command, validation_result)
            _write_json(attempt_root / 'classification.json', classification)
            attempt_result = {
                'attempt': attempt,
                'status': 'validation_failed',
                'retryable': bool(classification.get('retryable')),
                'reason': classification.get('reason') or 'validation failed',
                'failure_class': classification.get('failure_class'),
                'signature': classification.get('signature'),
            }
            _write_json(attempt_root / 'result.json', attempt_result)
            attempts.append(attempt_result)
            final_status = 'retrying' if attempt_result['retryable'] and attempt < attempts_allowed else 'failed'
            final_reason = attempt_result['reason']
            if not attempt_result['retryable']:
                break
        except ValueError as exc:
            attempt_result = {
                'attempt': attempt,
                'status': 'scope_blocked',
                'retryable': False,
                'reason': str(exc),
            }
            _write_json(attempt_root / 'result.json', attempt_result)
            attempts.append(attempt_result)
            final_status = 'failed'
            final_reason = attempt_result['reason']
            break
        finally:
            if temp_root is not None:
                shutil.rmtree(temp_root, ignore_errors=True)
    else:
        final_status = 'budget_exhausted'
        final_reason = 'attempt_budget_exhausted'

    summary = {
        'ok': final_status == 'passed',
        'run_id': run_id,
        'status': final_status,
        'reason': final_reason,
        'attempt_count': len(attempts),
        'attempts': attempts,
        'packet': {
            'project_id': packet.get('project_id'),
            'target_root': packet.get('target_root'),
            'task': packet.get('task'),
        },
        'artifacts_path': str(artifact_root.relative_to(REPO_ROOT)).replace('\\', '/'),
    }
    _write_json(artifact_root / 'result.json', summary)
    return summary
