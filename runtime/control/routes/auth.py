from fastapi import APIRouter, HTTPException

from schemas.auth_schema import LoginRequest
from services.auth_service import issue_token

router = APIRouter()


@router.post("/auth/login")
def login(payload: LoginRequest):
    try:
        return issue_token(payload.username)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
