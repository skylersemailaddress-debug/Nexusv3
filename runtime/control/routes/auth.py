from fastapi import APIRouter
from schemas.auth_schema import LoginRequest
from services.auth_service import issue_token

router = APIRouter()

@router.post("/auth/login")
def login(payload: LoginRequest):
    return issue_token(payload.username)
