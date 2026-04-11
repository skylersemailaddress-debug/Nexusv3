from dataclasses import dataclass
import secrets
import time
import uuid

from services.auth_policy import ROLE_ADMIN, is_valid_role
from services.env_service import get_runtime_config
from storage import (
    create_runtime_session,
    delete_stale_runtime_sessions,
    read_runtime_accounts,
    read_runtime_session_by_token,
    read_runtime_sessions,
    revoke_runtime_session,
    revoke_runtime_session_by_id,
    revoke_runtime_sessions_by_username,
    update_runtime_account_active,
)


@dataclass
class AuthUser:
    username: str
    role: str
    token_type: str = "session"


def _all_accounts() -> list[dict[str, str | int]]:
    return read_runtime_accounts()


def _active_accounts() -> list[dict[str, str | int]]:
    accounts = []
    for account in _all_accounts():
        if account.get("is_active") != 1:
            continue
        role = str(account.get("role", ""))
        if not is_valid_role(role):
            continue
        accounts.append(account)
    return accounts


def _accounts_by_username() -> dict[str, dict[str, str | int]]:
    return {account["username"]: account for account in _active_accounts()}


def _accounts_by_token() -> dict[str, dict[str, str | int]]:
    return {account["token"]: account for account in _active_accounts()}


def _all_accounts_by_username() -> dict[str, dict[str, str | int]]:
    return {account["username"]: account for account in _all_accounts()}


def _session_ttl_seconds() -> int:
    return int(get_runtime_config()["session_ttl_seconds"])


def _session_ended_retention_seconds() -> int:
    return int(get_runtime_config()["session_ended_retention_seconds"])


def _new_session_token() -> str:
    return f"nxs_{secrets.token_urlsafe(24)}"


def _resolve_session_token(token: str) -> AuthUser | None:
    row = read_runtime_session_by_token(token)
    if row is None:
        return None
    if int(row.get("is_active", 0)) != 1:
        return None
    if not is_valid_role(str(row.get("role", ""))):
        return None
    if row.get("revoked_at") is not None:
        return None
    if int(row["expires_at"]) <= int(time.time()):
        return None
    return AuthUser(username=str(row["username"]), role=str(row["role"]), token_type="session")


def _resolve_legacy_account_token(token: str) -> AuthUser | None:
    row = _accounts_by_token().get(token)
    if not row:
        return None
    return AuthUser(username=str(row["username"]), role=str(row["role"]), token_type="legacy")


def resolve_token(token: str | None) -> AuthUser | None:
    if not token:
        return None
    return _resolve_session_token(token) or _resolve_legacy_account_token(token)


def validate_token(token: str | None) -> AuthUser:
    user = resolve_token(token)
    if user is None:
        raise ValueError("Unauthorized")
    return user


def issue_token(username: str) -> dict:
    row = _accounts_by_username().get(username)
    if row is None:
        raise ValueError("Unknown runtime account")

    created_at = int(time.time())
    expires_at = created_at + _session_ttl_seconds()
    session_id = str(uuid.uuid4())
    token = _new_session_token()
    create_runtime_session(session_id, str(row["username"]), token, created_at, expires_at)
    return {
        "session_id": session_id,
        "access_token": token,
        "token_type": "bearer",
        "role": row["role"],
        "expires_at": expires_at,
    }


def revoke_token(token: str) -> dict[str, str | int] | None:
    if _resolve_legacy_account_token(token) is not None:
        raise ValueError("Legacy runtime account tokens cannot be revoked")
    return revoke_runtime_session(token, int(time.time()))


def list_runtime_account_summaries() -> list[dict[str, str | int]]:
    return [
        {
            "username": str(account["username"]),
            "role": str(account["role"]),
            "is_active": int(account["is_active"]),
        }
        for account in _all_accounts()
    ]


def list_runtime_session_summaries() -> list[dict[str, str | int]]:
    now_ts = int(time.time())
    return [
        {
            "id": str(session["id"]),
            "username": str(session["username"]),
            "role": str(session["role"]),
            "account_is_active": int(session["is_active"]),
            "created_at": int(session["created_at"]),
            "expires_at": int(session["expires_at"]),
            "revoked_at": session["revoked_at"],
            "state": (
                "revoked"
                if session["revoked_at"] is not None
                else "expired"
                if int(session["expires_at"]) <= now_ts
                else "active"
            ),
        }
        for session in read_runtime_sessions()
    ]


def revoke_session_by_id(session_id: str) -> dict[str, str | int] | None:
    sessions = {session["id"]: session for session in read_runtime_sessions()}
    session = sessions.get(session_id)
    if session is None:
        return None
    if session.get("revoked_at") is not None:
        raise ValueError("Runtime session already revoked")
    return revoke_runtime_session_by_id(session_id, int(time.time()))


def revoke_sessions_for_username(username: str) -> dict[str, str | int] | None:
    account = _all_accounts_by_username().get(username)
    if account is None:
        return None
    now_ts = int(time.time())
    revoked_count = revoke_runtime_sessions_by_username(username, now_ts, now_ts)
    return {
        "username": username,
        "revoked_count": revoked_count,
    }


def cleanup_expired_sessions() -> dict[str, int]:
    retention_seconds = _session_ended_retention_seconds()
    deleted = delete_stale_runtime_sessions(int(time.time()), retention_seconds)
    return {
        "retention_seconds": retention_seconds,
        "expired_deleted_count": deleted["expired_deleted_count"],
        "revoked_deleted_count": deleted["revoked_deleted_count"],
        "deleted_count": deleted["expired_deleted_count"] + deleted["revoked_deleted_count"],
    }


def _active_admin_count() -> int:
    return sum(1 for account in _active_accounts() if account.get("role") == ROLE_ADMIN)


def _transition_account_active(username: str, *, from_active: int, to_active: int) -> dict[str, str | int] | None:
    account = _all_accounts_by_username().get(username)
    if account is None:
        return None
    current_active = int(account.get("is_active", 0))
    if current_active != from_active:
        state = "active" if current_active == 1 else "inactive"
        target = "active" if to_active == 1 else "inactive"
        raise ValueError(f"Invalid account transition: {state} -> {target}")
    if (
        from_active == 1
        and to_active == 0
        and account.get("role") == ROLE_ADMIN
        and _active_admin_count() <= 1
    ):
        raise ValueError("Cannot deactivate the last active admin account")
    return update_runtime_account_active(username, to_active)


def deactivate_runtime_account(username: str) -> dict[str, str | int] | None:
    return _transition_account_active(username, from_active=1, to_active=0)


def activate_runtime_account(username: str) -> dict[str, str | int] | None:
    return _transition_account_active(username, from_active=0, to_active=1)
