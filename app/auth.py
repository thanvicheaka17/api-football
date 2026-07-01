from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

from app.config import get_settings

API_KEY_HEADER = APIKeyHeader(name="API_KEY", auto_error=False)


def require_api_key(api_key: str | None = Security(API_KEY_HEADER)) -> None:
    settings = get_settings()
    if not settings.api_key:
        return
    if not api_key or api_key != settings.api_key:
        raise HTTPException(
            status_code=401,
            detail={"status": "failed", "message": "Unauthorized"},
        )
