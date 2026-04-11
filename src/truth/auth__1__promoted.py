from fastapi import Header, HTTPException, status
from app.settings import settings


def require_api_token(authorization: str | None = Header(default=None)) -> None:
    expected = f"Bearer {settings.api_bearer_token}"
    if authorization != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        )


def require_runner_secret(x_runner_secret: str | None = Header(default=None)) -> None:
    if x_runner_secret != settings.runner_shared_secret:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized runner",
        )
