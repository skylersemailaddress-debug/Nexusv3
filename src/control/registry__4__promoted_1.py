from pathlib import Path

from fastapi import APIRouter, Depends
from app.auth import require_api_token

router = APIRouter(
    prefix="/registry",
    tags=["registry"],
    dependencies=[Depends(require_api_token)],
)


@router.get("/capabilities")
def registry_capabilities():
    seed_path = Path(__file__).resolve().parents[4] / "registry" / "seed_capabilities.json"
    if seed_path.exists():
        import json
        with seed_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
    return []
