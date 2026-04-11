from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.auth import require_api_token
from app.services.briefing import build_context

router = APIRouter(
    prefix="/state",
    tags=["state"],
    dependencies=[Depends(require_api_token)],
)


class BuildContextRequest(BaseModel):
    project_id: str
    user_message: str


@router.post("/build-context")
def state_build_context(req: BuildContextRequest):
    return build_context(req.project_id, req.user_message)
