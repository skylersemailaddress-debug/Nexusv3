from fastapi import APIRouter, Depends, Header, HTTPException

from routes.auth_deps import get_current_user
from schemas.auth_schema import LoginRequest
from services.auth_service import issue_token, revoke_token
from services.observability_service import audit_write

router = APIRouter()


def _extract_bearer_token(authorization: str | None) -> str | None:
    if authorization and authorization.lower().startswith("bearer "):
        return authorization.split(" ", 1)[1].strip()
    return None


@router.post("/auth/login")
def login(payload: LoginRequest):
    try:
        result = issue_token(payload.username)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    actor = {"username": payload.username, "role": result["role"]}
    audit_write(
        actor,
        "auth.login",
        {
            "session_id": result["session_id"],
            "expires_at": result["expires_at"],
            "token_type": result["token_type"],
        },
    )
    return result


@router.post("/auth/logout")
def logout(
    user=Depends(get_current_user),
    authorization: str | None = Header(default=None),
):
    token = _extract_bearer_token(authorization)
    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        result = revoke_token(token)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if result is None:
        raise HTTPException(status_code=404, detail="Runtime session not found")

    audit_write(
        {"username": user.username, "role": user.role},
        "auth.logout",
        {
            "session_id": result["id"],
            "revoked_at": result["revoked_at"],
            "token_type": user.token_type,
        },
    )
    return {
        "result": "session revoked",
        "username": user.username,
        "session_id": result["id"],
        "revoked_at": result["revoked_at"],
    }
