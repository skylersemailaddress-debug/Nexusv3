from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from uuid import UUID

from ..db.session import get_db
from ..services.one_button_controller import run_one_button_build

router = APIRouter()

@router.post("/projects/{project_id}/one-button-build")
def one_button_build_route(project_id: UUID, payload: dict, db: Session = Depends(get_db)):
    mode = payload.get("mode", "build")
    text = payload.get("text", "")
    result = run_one_button_build(db, str(project_id), mode, text)
    return {"ok": True, "data": result, "meta": {}}
