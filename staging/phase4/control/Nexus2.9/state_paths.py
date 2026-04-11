from pathlib import Path


def _find_repo_root(start: Path) -> Path:
    for candidate in [start] + list(start.parents):
        if (candidate / "scripts" / "bootstrap-local-backend.ps1").exists():
            return candidate
        if (candidate / ".git").exists():
            return candidate
    # Fallback for local repo shape: C:\ODP\apps\api\app\core\state_paths.py -> repo root is parents[4]
    try:
        return start.parents[4]
    except Exception:
        return start.parent


REPO_ROOT = _find_repo_root(Path(__file__).resolve())
STATE_ROOT = REPO_ROOT / "state"
PROJECTS_STATE_ROOT = STATE_ROOT / "projects"
ARTIFACT_FILES_ROOT = STATE_ROOT / "artifacts"

MESSAGES_PATH = STATE_ROOT / "messages.json"
JOBS_PATH = STATE_ROOT / "jobs.json"
ARTIFACTS_PATH = STATE_ROOT / "artifacts.json"
CHECKPOINTS_PATH = STATE_ROOT / "checkpoints.json"
SUMMARY_PATH = STATE_ROOT / "current_objective.json"


def ensure_state_root() -> None:
    STATE_ROOT.mkdir(parents=True, exist_ok=True)
    PROJECTS_STATE_ROOT.mkdir(parents=True, exist_ok=True)
    ARTIFACT_FILES_ROOT.mkdir(parents=True, exist_ok=True)


def project_state_dir(project_id: str) -> Path:
    ensure_state_root()
    root = PROJECTS_STATE_ROOT / project_id
    root.mkdir(parents=True, exist_ok=True)
    return root


def project_summary_path(project_id: str) -> Path:
    return project_state_dir(project_id) / "summary.json"


def artifact_file_path(artifact_id: str) -> Path:
    ensure_state_root()
    return ARTIFACT_FILES_ROOT / f"{artifact_id}.json"
