from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
def health():
    return {"status": "ok"}

@router.get("/health/readiness")
def readiness():
    return {"status": "ready"}

@router.get("/health/liveness")
def liveness():
    return {"status": "alive"}
