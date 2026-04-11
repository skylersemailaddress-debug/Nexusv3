from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes.projects import router as projects_router
from .routes.messages import router as messages_router
from .routes.runs import router as runs_router
from .routes.auth import router as auth_router
from .routes.autobuilder import router as autobuilder_router
from .routes.autobuilder_runtime import router as autobuilder_runtime_router
from .routes.autobuilder_finalize import router as autobuilder_finalize_router
from .routes.ui_generator import router as ui_generator_router
from .routes.quality import router as quality_router
from .routes.ops import router as ops_router
from .routes.workers import router as workers_router
from .routes.agent import router as agent_router
from .routes.voice import router as voice_router
from .routes.one_button import router as one_button_router

app = FastAPI(title="Nexus API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/v1")
app.include_router(projects_router, prefix="/v1")
app.include_router(messages_router, prefix="/v1")
app.include_router(runs_router, prefix="/v1")
app.include_router(autobuilder_router, prefix="/v1")
app.include_router(autobuilder_runtime_router, prefix="/v1")
app.include_router(autobuilder_finalize_router, prefix="/v1")
app.include_router(ui_generator_router, prefix="/v1")
app.include_router(quality_router, prefix="/v1")
app.include_router(ops_router, prefix="/v1")
app.include_router(workers_router, prefix="/v1")
app.include_router(agent_router, prefix="/v1")
app.include_router(voice_router, prefix="/v1")
app.include_router(one_button_router, prefix="/v1")

@app.get("/health")
def health():
    return {"ok": True, "service": "nexus-api", "stage": "final_layer"}
