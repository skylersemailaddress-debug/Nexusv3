from fastapi.openapi.utils import get_openapi
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.bootstrap import bootstrap_system
from app.routes.health import router as health_router
from app.routes.protected import router as protected_router
from app.routes.projects import router as projects_router
from app.routes.resume import router as resume_router
from app.routes.state import router as state_router
from app.routes.memory import router as memory_router
from app.routes.messages import router as messages_router
from app.routes.state_update import router as state_update_router
from app.routes.jobs import router as jobs_router
from app.routes.runner import router as runner_router
from app.routes.repo import router as repo_router
from app.routes.logs import router as logs_router
from app.routes.ramble import router as ramble_router
from app.routes.checkpoints import router as checkpoints_router
from app.routes.registry import router as registry_router
from app.routes.orchestrate import router as orchestrate_router
from app.routes.artifacts import router as artifacts_router
from app.routes.devtools import router as devtools_router
from app.routes.system_exec import router as system_exec_router
from app.routes.system_state import router as system_state_router
from app.routes.frontend_compat import router as frontend_compat_router
from app.routes.activity import router as activity_router
from app.routes.automation import router as automation_router
from app.routes.automation_admin import router as automation_admin_router
from app.routes.connectors import router as connectors_router
from app.routes.admin_system import router as admin_system_router
from app.routes.admin_jobs import router as admin_jobs_router
from app.routes.admin_failures import router as admin_failures_router
from app.routes.admin_projects import router as admin_projects_router
from app.routes.admin_runners import router as admin_runners_router
from app.routes.metrics import router as metrics_router
from app.routes.plans import router as plans_router
from app.services.logging_config import configure_logging
from app.services.observability import RequestContextMiddleware
from app.settings import settings

configure_logging()


@asynccontextmanager
async def lifespan(_: FastAPI):
    bootstrap_system()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_middleware(RequestContextMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(protected_router)
app.include_router(projects_router)
app.include_router(resume_router)
app.include_router(state_router)
app.include_router(memory_router)
app.include_router(messages_router)
app.include_router(state_update_router)
app.include_router(jobs_router)
app.include_router(runner_router)
app.include_router(repo_router)
app.include_router(logs_router)
app.include_router(artifacts_router)
app.include_router(devtools_router)
app.include_router(registry_router)
app.include_router(orchestrate_router)
app.include_router(checkpoints_router)
app.include_router(ramble_router)
app.include_router(system_exec_router)
app.include_router(system_state_router)
app.include_router(frontend_compat_router)
app.include_router(activity_router)
app.include_router(automation_router)
app.include_router(automation_admin_router)
app.include_router(connectors_router)
app.include_router(admin_system_router)
app.include_router(admin_jobs_router)
app.include_router(admin_failures_router)
app.include_router(admin_projects_router)
app.include_router(admin_runners_router)
app.include_router(metrics_router)
app.include_router(plans_router)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(
        title=app.title,
        version=getattr(app, "version", "0.1.0"),
        description=getattr(app, "description", None),
        routes=app.routes,
    )
    components = schema.setdefault("components", {})
    security = components.setdefault("securitySchemes", {})
    security["apiBearer"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "API_BEARER_TOKEN",
        "description": "Use Authorization: Bearer <API_BEARER_TOKEN>",
    }
    security["runnerSecret"] = {
        "type": "apiKey",
        "in": "header",
        "name": "x-runner-secret",
        "description": "Runner secret for runner endpoints",
    }
    security["adminKey"] = {
        "type": "apiKey",
        "in": "header",
        "name": "x-admin-key",
        "description": "Admin key for system endpoints",
    }
    app.openapi_schema = schema
    return app.openapi_schema


app.openapi = custom_openapi
