from pathlib import Path
import sys
import time

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware

CONTROL_DIR = Path(__file__).resolve().parent
if str(CONTROL_DIR) not in sys.path:
    sys.path.insert(0, str(CONTROL_DIR))

from storage import init_db
from routes.health import router as health_router
from routes.auth import router as auth_router
from routes.actions import router as actions_router
from routes.dashboard import router as dashboard_router
from routes.workflows import router as workflow_router
from routes.ops import router as ops_router
from routes.auth_deps import extract_bearer_token
from services.auth_service import validate_token
from services.observability_service import log_request, new_request_id
from services.security_service import allow_request
from services.env_service import get_runtime_config

runtime_config = get_runtime_config()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in runtime_config["allowed_origins"].split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

init_db()


@app.middleware("http")
async def security_and_logging_middleware(request: Request, call_next):
    client_ip = request.client.host if request.client else "unknown"
    if not allow_request(client_ip):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    token = extract_bearer_token(request.headers.get("Authorization"))
    request.state.auth_user = None
    if token:
        try:
            request.state.auth_user = validate_token(token)
        except ValueError as exc:
            raise HTTPException(status_code=401, detail=str(exc)) from exc

    request_id = new_request_id()
    start = time.time()
    response = await call_next(request)
    duration_ms = int((time.time() - start) * 1000)

    response.headers["X-Request-Id"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Cache-Control"] = "no-store"

    log_request({
        "request_id": request_id,
        "method": request.method,
        "path": request.url.path,
        "status_code": response.status_code,
        "duration_ms": duration_ms,
        "client_ip": client_ip,
    })
    return response


app.include_router(health_router)
app.include_router(auth_router)
app.include_router(actions_router)
app.include_router(dashboard_router)
app.include_router(workflow_router)
app.include_router(ops_router)
