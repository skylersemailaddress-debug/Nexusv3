import os
from fastapi import Header, HTTPException, Request

from app.settings import settings

_ALLOWED_HOSTS = {"127.0.0.1", "localhost", "::1"}



def _require_local_access(request: Request) -> None:
    client_host = request.client.host if request.client else None
    if client_host not in _ALLOWED_HOSTS:
        raise HTTPException(status_code=403, detail="Local access only")



def require_api_token(
    request: Request,
    authorization: str | None = Header(default=None),
):
    _require_local_access(request)

    expected = f"Bearer {settings.api_bearer_token}"
    if authorization != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")

    return True



def require_runner_secret(
    request: Request,
    x_runner_secret: str | None = Header(default=None),
    authorization: str | None = Header(default=None),
):
    _require_local_access(request)

    expected_secret = settings.runner_shared_secret
    expected_bearer = f"Bearer {expected_secret}"
    if x_runner_secret != expected_secret and authorization != expected_bearer:
        raise HTTPException(status_code=401, detail="Unauthorized")

    return True

def _read_first_env(*keys: str, default: str | None = None) -> str | None:
    for key in keys:
        value = os.getenv(key)
        if value:
            return value
    return default

def _expected_api_authorization() -> str:
    token = _read_first_env("API_BEARER_TOKEN", "DEV_API_TOKEN", default="dev-api-token")
    return f"Bearer {token}"

def _expected_runner_secret() -> str:
    return _read_first_env("RUNNER_SECRET", default="dev-runner-secret")

def _expected_admin_key() -> str:
    return _read_first_env("ADMIN_KEY", default="dev-admin-key")

