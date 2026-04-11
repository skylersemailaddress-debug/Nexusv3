from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from app.auth import require_api_token
from app.services.repo_service import repo_apply_patch, repo_read, repo_search, repo_write

router = APIRouter(prefix="/repo", tags=["repo"], dependencies=[Depends(require_api_token)])

class RepoWriteRequest(BaseModel):
    path: str
    content: str
    create_dirs: bool = True

class RepoPatchRequest(BaseModel):
    path: str
    search: str
    replace: str
    expected_count: int | None = None

@router.get("/read")
def read_repo(path: str = Query(..., description="Repo-relative path")):
    return repo_read(path)

@router.get("/search")
def search_repo(query: str = Query(..., description="Search text"), limit: int = Query(20, ge=1, le=100)):
    return repo_search(query=query, limit=limit)

@router.post("/write")
def write_repo(req: RepoWriteRequest):
    return repo_write(req.path, req.content, req.create_dirs)

@router.post("/apply-patch")
def apply_patch(req: RepoPatchRequest):
    return repo_apply_patch(req.path, req.search, req.replace, req.expected_count)
