from fastapi import APIRouter
from app.settings import settings

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
def health():
    return {
        "ok": True,
        "app": settings.app_name,
    }


@router.get("/protected")
def protected_health():
    return {
        "ok": True,
        "protected": True,
    }
