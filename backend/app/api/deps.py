"""Shared API dependencies."""
from __future__ import annotations

from fastapi import Depends, Header, HTTPException, status

from app.core.config import Settings, get_settings


async def verify_api_key(
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    settings: Settings = Depends(get_settings),
) -> None:
    """Verify the API key from the X-API-Key header.

    In development (default key), the check is skipped.
    """
    # Skip in development/test with default key
    if settings.environment in ("development", "test") and settings.api_key == "change-me-in-production":
        return

    if x_api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )
