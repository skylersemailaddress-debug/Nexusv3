from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from app.settings import settings


@dataclass(frozen=True)
class RetryPolicy:
    name: str
    max_retries: int
    base_seconds: int
    max_seconds: int


_POLICIES = {
    "transient_network": RetryPolicy("network_backoff", 3, 15, 300),
    "dependency_unavailable": RetryPolicy("dependency_backoff", 4, 30, 600),
    "executor_unreachable": RetryPolicy("executor_recovery", 2, 20, 180),
    "timeout": RetryPolicy("timeout_backoff", 2, 45, 240),
    "serialization_error": RetryPolicy("serialization_repair", 1, 10, 60),
    "default": RetryPolicy("default_backoff", 1, int(settings.retry_backoff_base_seconds), int(settings.retry_backoff_max_seconds)),
}


def select_retry_policy(job: dict[str, Any], classification: dict[str, Any]) -> RetryPolicy:
    inputs = job.get("inputs") or {}
    explicit_name = inputs.get("retry_policy")
    if explicit_name:
        for policy in _POLICIES.values():
            if policy.name == explicit_name:
                return policy
    return _POLICIES.get(classification.get("failure_class"), _POLICIES["default"])


def effective_max_retries(job: dict[str, Any], policy: RetryPolicy) -> int:
    configured = int(job.get("max_retries") or 0)
    return configured if configured > 0 else policy.max_retries


def compute_backoff_seconds(attempt_number: int, policy: RetryPolicy) -> int:
    multiplier = max(0, attempt_number - 1)
    return min(policy.base_seconds * (2**multiplier), policy.max_seconds)


def plan_retry(job: dict[str, Any], classification: dict[str, Any], now: datetime | None = None) -> dict[str, Any]:
    retry_count = int(job.get("retry_count") or 0)
    next_retry_count = retry_count + 1
    policy = select_retry_policy(job, classification)
    max_retries = effective_max_retries(job, policy)
    retryable = bool(classification.get("retryable"))
    should_retry = retryable and next_retry_count <= max_retries
    current_time = now or datetime.now(timezone.utc)
    next_retry_at = None
    backoff_seconds = None
    if should_retry:
        backoff_seconds = compute_backoff_seconds(next_retry_count, policy)
        next_retry_at = current_time + timedelta(seconds=backoff_seconds)
    return {
        "retryable": retryable,
        "should_retry": should_retry,
        "policy": policy,
        "max_retries": max_retries,
        "next_retry_count": next_retry_count,
        "backoff_seconds": backoff_seconds,
        "next_retry_at": next_retry_at,
    }
