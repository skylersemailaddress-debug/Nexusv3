from fastapi import APIRouter, Depends
from app.auth import require_api_token

router = APIRouter(prefix="/protected", tags=["protected"])


@router.get("/ping", dependencies=[Depends(require_api_token)])
def protected_ping():
    return {"ok": True, "message": "authorized"}
