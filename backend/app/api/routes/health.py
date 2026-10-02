"""Health check endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.config import Settings, get_settings
from app.services.llm import LLMService

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    app: str
    version: str
    environment: str
    llm_model: str
    llm_reachable: bool


@router.get("/health", response_model=HealthResponse)
async def health_check(settings: Settings = Depends(get_settings)) -> HealthResponse:
    """Basic health check.

    Verifies the app is up and tries a lightweight LLM ping if a key is configured.
    """
    llm_reachable = False
    try:
        if settings.openai_api_key or settings.anthropic_api_key or settings.ollama_base_url:
            svc = LLMService(settings)
            llm_reachable = await svc.ping()
    except Exception:  # noqa: BLE001
        llm_reachable = False

    return HealthResponse(
        status="ok",
        app=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
        llm_model=settings.llm_model,
        llm_reachable=llm_reachable,
    )
