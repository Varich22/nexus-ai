"""LLM service — thin wrapper around LiteLLM for shared operations."""
from __future__ import annotations

import asyncio

from litellm import acompletion

from app.core.config import Settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class LLMService:
    """Shared LLM operations (ping, completion, etc.)."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def ping(self) -> bool:
        """Lightweight check that the configured LLM is reachable."""
        try:
            resp = await acompletion(
                model=self.settings.llm_model,
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=5,
                api_key=self.settings.openai_api_key,
                timeout=10,
            )
            return bool(resp.choices)
        except Exception as exc:  # noqa: BLE001
            logger.warning("llm_ping_failed", error=str(exc))
            return False

    async def complete(
        self,
        messages: list[dict],
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        """Simple non-streaming completion helper."""
        resp = await acompletion(
            model=self.settings.llm_model,
            messages=messages,
            temperature=temperature or self.settings.llm_temperature,
            max_tokens=max_tokens or self.settings.llm_max_tokens,
            api_key=self.settings.openai_api_key,
        )
        return resp.choices[0].message.content or ""
