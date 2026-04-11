from fastapi import APIRouter, Depends

from app.auth import require_api_token
from app.services.checkpoints import create_checkpoint

router = APIRouter(
    tags=["checkpoints"],
    dependencies=[Depends(require_api_token)],
)


@router.post("/projects/{project_id}/checkpoint")
def checkpoint_project(project_id: str):
    return create_checkpoint(project_id)


