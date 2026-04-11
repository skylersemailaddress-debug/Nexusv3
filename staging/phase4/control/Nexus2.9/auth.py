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
    x_nexus_client: str | None = Header(default=None),
):
    _require_local_access(request)

    expected = f"Bearer {settings.api_bearer_token}"
    if authorization == expected:
        return True

    if x_nexus_client == settings.web_client_id:
        return True

    raise HTTPException(status_code=401, detail="Unauthorized")



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

