from fastapi import APIRouter
from ..services.voice_runtime import start_voice_session, ingest_voice_utterance, commit_voice_to_project

router = APIRouter()

@router.post("/voice/start")
def voice_start_route(payload: dict):
    project_id = payload.get("project_id", "unknown")
    return {"ok": True, "data": start_voice_session(project_id), "meta": {}}

@router.post("/voice/ingest")
def voice_ingest_route(payload: dict):
    text = payload.get("text", "")
    return {"ok": True, "data": ingest_voice_utterance(text), "meta": {}}

@router.post("/voice/commit")
def voice_commit_route(payload: dict):
    session_id = payload.get("voice_session_id", "unknown")
    text = payload.get("text", "")
    return {"ok": True, "data": commit_voice_to_project(session_id, text), "meta": {}}
