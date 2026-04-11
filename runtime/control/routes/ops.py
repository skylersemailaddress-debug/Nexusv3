from pathlib import Path
import json
import time

from fastapi import APIRouter, Depends

from routes.auth_deps import require_admin
from services.observability_service import AUDIT_LOG, REQUEST_LOG

router = APIRouter()

@router.get("/ops/support-bundle")
def support_bundle(user=Depends(require_admin)):
    def tail_lines(path: Path, limit: int = 20):
        if not path.exists():
            return []
        lines = path.read_text(encoding="utf-8").splitlines()
        return lines[-limit:]

    return {
        "generated_at": int(time.time()),
        "actor": {"username": user.username, "role": user.role},
        "request_log_tail": tail_lines(REQUEST_LOG),
        "audit_log_tail": tail_lines(AUDIT_LOG),
    }
