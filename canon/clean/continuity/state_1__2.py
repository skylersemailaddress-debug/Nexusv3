from fastapi import APIRouter
from pydantic import BaseModel
from app.services.briefing import build_context

router = APIRouter(prefix="/state", tags=["state"])


class BuildContextRequest(BaseModel):
    project_id: str
    user_message: str


@router.post("/build-context")
def state_build_context(req: BuildContextRequest):
    return build_context(req.project_id, req.user_message)
