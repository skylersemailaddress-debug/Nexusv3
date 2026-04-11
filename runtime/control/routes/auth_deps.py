from fastapi import Header, HTTPException

from services.auth_policy import ROLE_ADMIN, has_required_role
from services.auth_service import resolve_token


def get_current_user(authorization: str | None = Header(default=None)):
    token = None
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()

    user = resolve_token(token)
    if user is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return user


def require_role(required_role: str, user=None, authorization: str | None = Header(default=None)):
    current = user or get_current_user(authorization)
    if not has_required_role(current.role, required_role):
        raise HTTPException(status_code=403, detail="Forbidden")
    return current


def require_admin(user=None, authorization: str | None = Header(default=None)):
    return require_role(ROLE_ADMIN, user=user, authorization=authorization)
