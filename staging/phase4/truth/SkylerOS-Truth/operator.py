from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def _parse_dt(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    text = str(value)
    try:
        dt = datetime.fromisoformat(text.replace('Z', '+00:00'))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _hours_since(value: Any) -> float | None:
    dt = _parse_dt(value)
    if not dt:
        return None
    return (datetime.now(timezone.utc) - dt).total_seconds() / 3600.0


def build_operator_state(now: dict[str, Any]) -> dict[str, Any]:
    blockers = now.get('blockers', []) or []
    recent_jobs = now.get('recent_jobs', []) or []
    recent_artifacts = now.get('recent_artifacts', []) or []
    recent_messages = now.get('recent_messages', []) or []
    relevant_memory = now.get('relevant_memory', []) or []
    objective = now.get('objective')
    next_step = now.get('next_step')

    failed_jobs = [job for job in recent_jobs if job.get('status') == 'failed']
    running_jobs = [job for job in recent_jobs if job.get('status') == 'running']
    queued_jobs = [job for job in recent_jobs if job.get('status') == 'queued']
    completed_jobs = [job for job in recent_jobs if job.get('status') == 'completed']

    checkpoint_artifacts = [a for a in recent_artifacts if a.get('kind') == 'checkpoint']
    ramble_artifacts = [a for a in recent_artifacts if a.get('kind') == 'ramble_capture']

    checkpoint_age_hours = _hours_since(checkpoint_artifacts[0].get('created_at')) if checkpoint_artifacts else None
    ramble_age_hours = _hours_since(ramble_artifacts[0].get('created_at')) if ramble_artifacts else None
    last_message_age_hours = _hours_since(recent_messages[-1].get('created_at')) if recent_messages else None

    suggestions: list[dict[str, Any]] = []

    if blockers:
        top = blockers[0]
        suggestions.append({
            'id': 'resolve_blocker',
            'priority': 'high',
            'kind': 'blocker_resolution',
            'title': f"Resolve blocker: {top.get('title')}",
            'reason': f"{len(blockers)} blocker(s) remain open; the most recent blocker is limiting forward progress.",
            'payload': {'blocker_id': top.get('id')},
        })

    if failed_jobs:
        job = failed_jobs[0]
        suggestions.append({
            'id': 'repair_failed_job',
            'priority': 'high',
            'kind': 'job_recovery',
            'title': f"Repair failed job: {job.get('capability_id')}",
            'reason': 'A recent job failed and should be inspected before additional automation compounds the error.',
            'payload': {'job_id': job.get('id')},
        })

    if next_step:
        suggestions.append({
            'id': 'execute_next_step',
            'priority': 'high' if not blockers else 'medium',
            'kind': 'next_step',
            'title': next_step.get('title'),
            'reason': 'This is the currently linked next step for the active objective.',
            'payload': {'next_step_id': next_step.get('id'), 'objective_id': objective.get('id') if objective else None},
        })

    if queued_jobs and not running_jobs:
        suggestions.append({
            'id': 'drain_queue',
            'priority': 'medium',
            'kind': 'execution',
            'title': f"Work the execution queue ({len(queued_jobs)} queued)",
            'reason': 'Queued jobs exist without active execution pressure.',
            'payload': {'queued_job_ids': [job.get('id') for job in queued_jobs[:5]]},
        })

    if checkpoint_age_hours is None or checkpoint_age_hours > 12:
        suggestions.append({
            'id': 'capture_checkpoint',
            'priority': 'medium',
            'kind': 'checkpoint',
            'title': 'Capture a fresh checkpoint',
            'reason': 'The project lacks a recent checkpoint, which weakens resume quality and compression readiness.',
            'payload': {'project_id': now.get('project', {}).get('id')},
        })

    if ramble_age_hours is None and recent_messages:
        suggestions.append({
            'id': 'capture_ramble',
            'priority': 'low',
            'kind': 'ramble',
            'title': 'Capture a freeform ramble input',
            'reason': 'No ramble capture exists yet; freeform capture improves idea extraction and operator awareness.',
            'payload': {'project_id': now.get('project', {}).get('id')},
        })

    if not relevant_memory:
        suggestions.append({
            'id': 'strengthen_memory',
            'priority': 'medium',
            'kind': 'memory',
            'title': 'Upsert a durable project memory',
            'reason': 'No relevant durable memory surfaced for this context; adding one improves future continuity.',
            'payload': {'scope': 'project'},
        })

    if objective and completed_jobs and not blockers:
        suggestions.append({
            'id': 'chain_workflow',
            'priority': 'medium',
            'kind': 'workflow',
            'title': 'Chain the next workflow move',
            'reason': 'Execution is succeeding and no blockers are open, so the system can move beyond single-step operation.',
            'payload': {
                'objective_id': objective.get('id'),
                'recent_completed_job_ids': [job.get('id') for job in completed_jobs[:3]],
            },
        })

    priority_order = {'high': 0, 'medium': 1, 'low': 2}
    deduped: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in suggestions:
        key = item['id']
        if key not in seen:
            seen.add(key)
            deduped.append(item)
    deduped.sort(key=lambda item: (priority_order.get(item['priority'], 9), item['title']))

    status_line = 'stable'
    if blockers or failed_jobs:
        status_line = 'attention_required'
    elif queued_jobs or running_jobs:
        status_line = 'active_execution'

    summary_parts = []
    if objective:
        summary_parts.append(f"Objective: {objective.get('title')}")
    if next_step:
        summary_parts.append(f"Next: {next_step.get('title')}")
    if blockers:
        summary_parts.append(f"Open blockers: {len(blockers)}")
    if queued_jobs or running_jobs:
        summary_parts.append(f"Queue: {len(queued_jobs)} queued / {len(running_jobs)} running")
    if relevant_memory:
        summary_parts.append(f"Memory: {len(relevant_memory)} signal(s)")
    if checkpoint_artifacts:
        summary_parts.append('Checkpoint present')

    workflow_chain = []
    if deduped:
        workflow_chain = [item['title'] for item in deduped[:3]]

    return {
        'status': status_line,
        'summary': ' | '.join(summary_parts) if summary_parts else 'No operator summary available.',
        'prioritized_actions': deduped[:5],
        'workflow_chain': workflow_chain,
        'signals': {
            'open_blockers': len(blockers),
            'failed_jobs': len(failed_jobs),
            'queued_jobs': len(queued_jobs),
            'running_jobs': len(running_jobs),
            'completed_jobs': len(completed_jobs),
            'recent_messages': len(recent_messages),
            'memory_signals': len(relevant_memory),
            'checkpoint_age_hours': checkpoint_age_hours,
            'ramble_age_hours': ramble_age_hours,
            'last_message_age_hours': last_message_age_hours,
        },
        'richer_summary': {
            'objective_title': objective.get('title') if objective else None,
            'next_step_title': next_step.get('title') if next_step else None,
            'top_blocker': blockers[0].get('title') if blockers else None,
            'top_memory_titles': [item.get('title') for item in relevant_memory[:3]],
            'workflow_readiness': 'ready' if objective and not blockers else 'blocked' if blockers else 'forming',
        },
    }
