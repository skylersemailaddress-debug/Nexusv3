from dataclasses import dataclass

from services.auth_policy import ROLE_ADMIN, is_valid_role
from storage import read_runtime_accounts, update_runtime_account_active


@dataclass
class AuthUser:
    username: str
    role: str


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


def resolve_token(token: str | None) -> AuthUser | None:
    if not token:
        return None
    row = _accounts_by_token().get(token)
    if not row:
        return None
    return AuthUser(username=str(row["username"]), role=str(row["role"]))


def issue_token(username: str) -> dict:
    row = _accounts_by_username().get(username)
    if row is None:
        raise ValueError("Unknown runtime account")
    return {"access_token": row["token"], "token_type": "bearer", "role": row["role"]}


def list_runtime_account_summaries() -> list[dict[str, str | int]]:
    return [
        {
            "username": str(account["username"]),
            "role": str(account["role"]),
            "is_active": int(account["is_active"]),
        }
        for account in _all_accounts()
    ]


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
