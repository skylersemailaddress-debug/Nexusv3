
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from app.auth import require_api_token
from app.services.devtools import (
    apply_generated_code,
    enqueue_generated_validation,
    enqueue_lint_job,
    enqueue_script_job,
    enqueue_test_job,
    evaluate_job_result,
    generate_code_packet,
    retry_job_step,
)

router = APIRouter(prefix="/dev", tags=["dev"], dependencies=[Depends(require_api_token)])

class ScriptRunRequest(BaseModel):
    project_id: str
    command: str
    requested_by: str | None = None
    job_id: str | None = None
    approval_mode: str = "auto_read"

class TestRunRequest(BaseModel):
    project_id: str
    command: str = "pytest -q"
    requested_by: str | None = None
    job_id: str | None = None
    approval_mode: str = "auto_read"

class LintRunRequest(BaseModel):
    project_id: str
    command: str = "python -m compileall apps"
    requested_by: str | None = None
    job_id: str | None = None
    approval_mode: str = "auto_read"

class GenerateCodeRequest(BaseModel):
    project_id: str
    task: str
    target_paths: list[str] = Field(default_factory=list)
    acceptance_criteria: list[str] = Field(default_factory=list)
    approval_mode: str = "suggest_only"

class ApplyGeneratedCodeRequest(BaseModel):
    project_id: str
    artifact_id: str
    requested_by: str | None = None
    approval_mode: str = "manual"
    create_backup: bool = True

class ValidateGeneratedCodeRequest(BaseModel):
    project_id: str
    artifact_id: str
    command: str
    requested_by: str | None = None
    approval_mode: str = "auto_read"

class EvaluateJobRequest(BaseModel):
    job_id: str

class RetryJobRequest(BaseModel):
    job_id: str
    requested_by: str | None = None

@router.post('/run-script')
def run_script(req: ScriptRunRequest):
    return enqueue_script_job(req.project_id, req.command, req.requested_by, req.job_id, approval_mode=req.approval_mode)

@router.post('/run-test')
def run_test(req: TestRunRequest):
    return enqueue_test_job(req.project_id, req.command, req.requested_by, req.job_id, approval_mode=req.approval_mode)

@router.post('/run-lint')
def run_lint(req: LintRunRequest):
    return enqueue_lint_job(req.project_id, req.command, req.requested_by, req.job_id, approval_mode=req.approval_mode)

@router.post('/generate-code')
def generate_code(req: GenerateCodeRequest):
    return generate_code_packet(req.project_id, req.task, req.target_paths, req.acceptance_criteria, approval_mode=req.approval_mode)

@router.post('/apply-generated-code')
def apply_generated(req: ApplyGeneratedCodeRequest):
    return apply_generated_code(req.project_id, req.artifact_id, req.requested_by, req.approval_mode, req.create_backup)

@router.post('/validate-generated-code')
def validate_generated(req: ValidateGeneratedCodeRequest):
    return enqueue_generated_validation(req.project_id, req.artifact_id, req.command, req.requested_by, req.approval_mode)

@router.post('/evaluate-job')
def evaluate_job(req: EvaluateJobRequest):
    return evaluate_job_result(req.job_id)

@router.post('/retry-job')
def retry_job(req: RetryJobRequest):
    return retry_job_step(req.job_id, req.requested_by)
