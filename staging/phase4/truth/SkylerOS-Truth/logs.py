from fastapi import APIRouter, Depends, Query
from app.auth import require_api_token
from app.services.log_service import tail_logs

router = APIRouter(
    prefix="/logs",
    tags=["logs"],
    dependencies=[Depends(require_api_token)],
)


@router.get("/tail")
def logs_tail(limit: int = Query(100, ge=1, le=1000)):
    return tail_logs(limit=limit)
