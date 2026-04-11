from fastapi import APIRouter, HTTPException

from storage import check_storage_ready

router = APIRouter()


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/health/readiness")
def readiness():
    try:
        storage = check_storage_ready()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Storage readiness failed: {exc}") from exc
    return {"status": "ready", "storage": storage}


@router.get("/health/liveness")
def liveness():
    return {"status": "alive"}
