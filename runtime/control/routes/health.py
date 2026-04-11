from fastapi import APIRouter, HTTPException

from services.observability_service import record_event
from storage import check_storage_ready

router = APIRouter()


@router.get("/health")
def health():
    record_event("health.check")
    return {"status": "ok"}


@router.get("/health/readiness")
def readiness():
    try:
        storage = check_storage_ready()
    except Exception as exc:
        record_event("health.readiness", detail={"detail": str(exc)}, status="error")
        raise HTTPException(status_code=503, detail=f"Storage readiness failed: {exc}") from exc
    record_event("health.readiness", detail={"storage": storage})
    return {"status": "ready", "storage": storage}


@router.get("/health/liveness")
def liveness():
    record_event("health.liveness")
    return {"status": "alive"}
