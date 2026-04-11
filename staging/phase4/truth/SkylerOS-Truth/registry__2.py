
from fastapi import APIRouter, Depends
from app.auth import require_api_token

router = APIRouter(prefix="/registry", tags=["registry"], dependencies=[Depends(require_api_token)])

@router.get("/capabilities")
def list_capabilities():
    return {
        "ok": True,
        "capabilities": [
            {"id": "state.build_context", "name": "Build Context", "description": "Build project context for the current request.", "kind": "state"},
            {"id": "operator.plan", "name": "Operator Plan", "description": "Generate prioritized next actions, workflow chain suggestions, and richer operator summaries.", "kind": "operator"},
            {"id": "dev.generate_code", "name": "Generate Draft Patch", "description": "Create concrete draft file changes and a code packet artifact for a development task.", "kind": "dev"},
            {"id": "dev.apply_patch", "name": "Apply Generated Patch", "description": "Apply a generated code packet artifact into the repo with backups.", "kind": "dev"},
            {"id": "dev.evaluate_result", "name": "Evaluate Job Result", "description": "Summarize a completed or failed job result for developer workflows.", "kind": "dev"},
            {"id": "dev.run_test", "name": "Run Validation", "description": "Queue a validation command against generated code.", "kind": "dev"},
            {"id": "dev.retry_step", "name": "Retry Job", "description": "Requeue a retryable developer job.", "kind": "dev"},
        ],
    }
