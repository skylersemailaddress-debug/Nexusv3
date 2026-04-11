from dataclasses import dataclass

TOKENS = {
    "dev-operator-token": {"username": "operator", "role": "operator"},
    "dev-admin-token": {"username": "admin", "role": "admin"},
}

@dataclass
class AuthUser:
    username: str
    role: str

def resolve_token(token: str | None) -> AuthUser | None:
    if not token:
        return None
    row = TOKENS.get(token)
    if not row:
        return None
    return AuthUser(username=row["username"], role=row["role"])

def issue_token(username: str) -> dict:
    if username == "admin":
        return {"access_token": "dev-admin-token", "token_type": "bearer", "role": "admin"}
    return {"access_token": "dev-operator-token", "token_type": "bearer", "role": "operator"}
