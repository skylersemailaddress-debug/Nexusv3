from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


class TestActionRequest(BaseModel):
    message: Optional[str] = "ping"


app = FastAPI(title="Nexus Runtime Control API", version="0.1.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/action/test")
def action_test(payload: Optional[TestActionRequest] = None):
    message = "working"
    if payload and payload.message:
        return {"result": message, "echo": payload.message}
    return {"result": message}

@app.get("/dashboard/status")
def dashboard_status():
    return {
        "status": "ok",
        "system": "Nexus Runtime",
        "api": "healthy",
        "ui": "expected_on_5173",
        "next_step": "wire first real command center feature"
    }
