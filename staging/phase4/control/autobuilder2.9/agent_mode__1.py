def derive_agent_action_plan(request_text: str) -> dict:
    actions = []
    lowered = request_text.lower()
    if "build" in lowered:
        actions.append("run_codegen")
    if "install" in lowered:
        actions.append("run_dependency_install")
    if "deploy" in lowered:
        actions.append("prepare_deployment")
    if "open browser" in lowered or "preview" in lowered:
        actions.append("prepare_browser_validation")
    return {
        "actions": actions or ["analyze_request"],
        "status": "planned"
    }

def enforce_agent_guardrails(actions: list[str]) -> dict:
    risky = [a for a in actions if a in ("prepare_deployment",)]
    return {
        "actions": actions,
        "approval_required": risky,
        "status": "guarded"
    }
