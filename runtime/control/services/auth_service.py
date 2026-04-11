from dataclasses import dataclass

from services.auth_policy import is_valid_role
from storage import read_runtime_accounts


@dataclass
class AuthUser:
    username: str
    role: str


def _active_accounts() -> list[dict[str, str | int]]:
    accounts = []
    for account in read_runtime_accounts():
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
        for account in read_runtime_accounts()
    ]
