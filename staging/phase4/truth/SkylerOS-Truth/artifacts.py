from fastapi import APIRouter, Depends, Query
from app.auth import require_api_token
from app.services.artifact_service import list_artifacts

router = APIRouter(prefix="/artifacts", tags=["artifacts"], dependencies=[Depends(require_api_token)])

@router.get("/list")
def artifacts_list(project_id: str | None = Query(default=None), kind: str | None = Query(default=None), limit: int = Query(default=50, ge=1, le=200)):
    return list_artifacts(project_id=project_id, kind=kind, limit=limit)
