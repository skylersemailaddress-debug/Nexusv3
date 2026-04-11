from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.auth import require_api_token
from app.services.ramble import capture_ramble

router = APIRouter(
    tags=["ramble"],
    dependencies=[Depends(require_api_token)],
)


class RambleRequest(BaseModel):
    content: str
    meta: dict = Field(default_factory=dict)


@router.post("/projects/{project_id}/ramble")
def ramble_project(project_id: str, req: RambleRequest):
    return capture_ramble(project_id, req.content, req.meta)
