from fastapi import Header, HTTPException, Request

from services.auth_policy import ROLE_ADMIN, has_required_role
from services.auth_service import validate_token


def extract_bearer_token(authorization: str | None) -> str | None:
    if authorization and authorization.lower().startswith("bearer "):
        return authorization.split(" ", 1)[1].strip()
    return None


def get_current_user(
    request: Request,
    authorization: str | None = Header(default=None),
):
    current = getattr(request.state, "auth_user", None)
    if current is not None:
        return current

    token = extract_bearer_token(authorization)
    try:
        return validate_token(token)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


def require_role(required_role: str, request: Request, user=None, authorization: str | None = Header(default=None)):
    current = user or get_current_user(request, authorization)
    if not has_required_role(current.role, required_role):
        raise HTTPException(status_code=403, detail="Forbidden")
    return current


def require_admin(request: Request, user=None, authorization: str | None = Header(default=None)):
    return require_role(ROLE_ADMIN, request, user=user, authorization=authorization)
