from fastapi import APIRouter, Depends, Header, HTTPException

from routes.auth_deps import get_current_user
from schemas.auth_schema import LoginRequest
from services.auth_service import issue_token, revoke_token

router = APIRouter()


def _extract_bearer_token(authorization: str | None) -> str | None:
    if authorization and authorization.lower().startswith("bearer "):
        return authorization.split(" ", 1)[1].strip()
    return None


@router.post("/auth/login")
def login(payload: LoginRequest):
    try:
        return issue_token(payload.username)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


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

    return {
        "result": "session revoked",
        "username": user.username,
        "revoked_at": result["revoked_at"],
    }
