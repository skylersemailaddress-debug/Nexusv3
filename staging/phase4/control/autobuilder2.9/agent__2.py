from fastapi import APIRouter

from ..services.agent_mode import derive_agent_action_plan, enforce_agent_guardrails

router = APIRouter()

@router.post("/agent/plan")
def agent_plan_route(payload: dict):
    text = payload.get("text", "")
    plan = derive_agent_action_plan(text)
    guarded = enforce_agent_guardrails(plan.get("actions", []))
    return {"ok": True, "data": guarded, "meta": {}}
