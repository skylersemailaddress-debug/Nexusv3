from dataclasses import dataclass


DEFAULT_ACCOUNTS = {
    "operator": {"username": "operator", "role": "operator", "token": "dev-operator-token"},
    "admin": {"username": "admin", "role": "admin", "token": "dev-admin-token"},
}


@dataclass
class AuthUser:
    username: str
    role: str


def _accounts_by_username() -> dict[str, dict[str, str]]:
    return DEFAULT_ACCOUNTS


def _accounts_by_token() -> dict[str, dict[str, str]]:
    return {account["token"]: account for account in _accounts_by_username().values()}


def resolve_token(token: str | None) -> AuthUser | None:
    if not token:
        return None
    row = _accounts_by_token().get(token)
    if not row:
        return None
    return AuthUser(username=row["username"], role=row["role"])


def issue_token(username: str) -> dict:
    row = _accounts_by_username().get(username)
    if row is None:
        raise ValueError("Unknown runtime account")
    return {"access_token": row["token"], "token_type": "bearer", "role": row["role"]}
