from __future__ import annotations

from pathlib import Path
from typing import Iterable
import difflib
import os

REPO_ROOT = Path(os.getenv("SKYLER_REPO_ROOT", "/app")).resolve()

TEXT_EXTENSIONS = {
    ".py", ".ps1", ".json", ".md", ".txt", ".yaml", ".yml",
    ".toml", ".ini", ".sql", ".js", ".ts", ".tsx", ".jsx",
    ".html", ".css", ".dockerfile", ".sh", ".bat"
}

SKIP_DIRS = {
    ".git", ".venv", "venv", "__pycache__", ".pytest_cache",
    ".mypy_cache", ".ruff_cache", "node_modules"
}


def _is_within_repo(path: Path) -> bool:
    try:
        path.resolve().relative_to(REPO_ROOT)
        return True
    except Exception:
        return False


def _safe_path(rel_path: str) -> Path:
    if not rel_path:
        raise ValueError("path is required")
    candidate = (REPO_ROOT / rel_path).resolve()
    if not _is_within_repo(candidate):
        raise ValueError("path escapes repo root")
    return candidate


def _iter_files(base: Path) -> Iterable[Path]:
    for path in base.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        yield path


def _is_text_file(path: Path) -> bool:
    suffix = path.suffix.lower()
    return suffix in TEXT_EXTENSIONS or path.name.lower() == "dockerfile"


def repo_read(rel_path: str) -> dict:
    path = _safe_path(rel_path)
    if not path.exists():
        return {"ok": False, "error": f"Path not found: {rel_path}"}
    if path.is_dir():
        items = []
        for child in sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
            if child.name in SKIP_DIRS:
                continue
            items.append({
                "name": child.name,
                "path": str(child.relative_to(REPO_ROOT)).replace("\\", "/"),
                "kind": "dir" if child.is_dir() else "file",
            })
        return {"ok": True, "path": str(path.relative_to(REPO_ROOT)).replace("\\", "/"), "kind": "dir", "items": items}
    if not _is_text_file(path):
        return {"ok": False, "error": f"File type not allowed for read: {path.name}"}
    content = path.read_text(encoding="utf-8", errors="replace")
    return {"ok": True, "path": str(path.relative_to(REPO_ROOT)).replace("\\", "/"), "kind": "file", "content": content}


def repo_search(query: str, limit: int = 20) -> dict:
    if not query or not query.strip():
        return {"ok": False, "error": "query is required"}
    needle = query.lower()
    results = []
    for path in _iter_files(REPO_ROOT):
        if not _is_text_file(path):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        for idx, line in enumerate(text.splitlines(), start=1):
            if needle in line.lower():
                results.append({"path": str(path.relative_to(REPO_ROOT)).replace("\\", "/"), "line": idx, "snippet": line.strip()})
                if len(results) >= limit:
                    return {"ok": True, "query": query, "items": results}
    return {"ok": True, "query": query, "items": results}


def repo_write(rel_path: str, content: str, create_dirs: bool = True) -> dict:
    path = _safe_path(rel_path)
    existed = path.exists()
    previous_content = None
    if existed:
        if path.is_dir():
            return {"ok": False, "error": f"Cannot overwrite directory: {rel_path}"}
        if not _is_text_file(path):
            return {"ok": False, "error": f"File type not allowed for write: {path.name}"}
        previous_content = path.read_text(encoding="utf-8", errors="replace")
    elif create_dirs:
        path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    diff_preview = []
    if previous_content is not None and previous_content != content:
        diff_preview = list(difflib.unified_diff(previous_content.splitlines(), content.splitlines(), fromfile=f"a/{rel_path}", tofile=f"b/{rel_path}", lineterm=""))[:200]
    return {"ok": True, "path": str(path.relative_to(REPO_ROOT)).replace("\\", "/"), "created": not existed, "bytes_written": len(content.encode("utf-8")), "diff_preview": diff_preview}


def repo_apply_patch(rel_path: str, search: str, replace: str, expected_count: int | None = None) -> dict:
    path = _safe_path(rel_path)
    if not path.exists():
        return {"ok": False, "error": f"Path not found: {rel_path}"}
    if path.is_dir():
        return {"ok": False, "error": f"Cannot patch directory: {rel_path}"}
    if not _is_text_file(path):
        return {"ok": False, "error": f"File type not allowed for patch: {path.name}"}
    original = path.read_text(encoding="utf-8", errors="replace")
    match_count = original.count(search)
    if match_count == 0:
        return {"ok": False, "error": "search text not found", "path": rel_path}
    if expected_count is not None and match_count != expected_count:
        return {"ok": False, "error": f"expected {expected_count} matches but found {match_count}", "path": rel_path, "match_count": match_count}
    updated = original.replace(search, replace)
    path.write_text(updated, encoding="utf-8")
    diff_preview = list(difflib.unified_diff(original.splitlines(), updated.splitlines(), fromfile=f"a/{rel_path}", tofile=f"b/{rel_path}", lineterm=""))[:200]
    return {"ok": True, "path": str(path.relative_to(REPO_ROOT)).replace("\\", "/"), "match_count": match_count, "diff_preview": diff_preview}
