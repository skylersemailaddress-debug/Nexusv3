from fastapi import APIRouter, Depends
from app.auth import require_api_token
from app.services.state_builder import get_project_now
from app.services.briefing import build_brief

router = APIRouter(
    prefix="/projects",
    tags=["projects"],
    dependencies=[Depends(require_api_token)],
)


@router.get("/{project_id}/now")
def project_now(project_id: str):
    return get_project_now(project_id)


@router.get("/{project_id}/brief")
def project_brief(project_id: str):
    return build_brief(project_id)


@router.get("/{project_id}/what-changed")
def project_what_changed(project_id: str):
    brief = build_brief(project_id)
    if not brief.get("ok"):
        return brief
    return {
        "ok": True,
        "project_id": project_id,
        "what_changed": brief["what_changed"],
    }
