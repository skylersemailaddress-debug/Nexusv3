from fastapi import FastAPI
from app.routes.health import router as health_router
from app.routes.protected import router as protected_router
from app.routes.projects import router as projects_router
from app.routes.resume import router as resume_router
from app.routes.state import router as state_router
from app.routes.memory import router as memory_router
from app.routes.messages import router as messages_router
from app.routes.state_update import router as state_update_router
from app.routes.jobs import router as jobs_router
from app.routes.repo import router as repo_router
from app.routes.logs import router as logs_router
from app.routes.ramble import router as ramble_router
from app.routes.checkpoints import router as checkpoints_router
from app.routes.registry import router as registry_router
from app.routes.orchestrate import router as orchestrate_router
from app.routes.artifacts import router as artifacts_router
from app.routes.devtools import router as devtools_router
from app.services.logging_config import configure_logging
from app.settings import settings

configure_logging()

app = FastAPI(title=settings.app_name)
app.include_router(health_router)
app.include_router(protected_router)
app.include_router(projects_router)
app.include_router(resume_router)
app.include_router(state_router)
app.include_router(memory_router)
app.include_router(messages_router)
app.include_router(state_update_router)
app.include_router(jobs_router)
app.include_router(repo_router)
app.include_router(logs_router)
app.include_router(artifacts_router)
app.include_router(devtools_router)
app.include_router(registry_router)
app.include_router(orchestrate_router)
app.include_router(checkpoints_router)
app.include_router(ramble_router)
