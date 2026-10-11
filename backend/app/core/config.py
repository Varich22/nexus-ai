"""Application settings — loaded from environment variables / .env file."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Global settings. Read from env vars or .env file."""

    project_root = Path(__file__).resolve().parents[3]
    model_config = SettingsConfigDict(
        env_file=str(project_root / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ----- App -----
    app_name: str = "nexus-ai"
    app_version: str = "0.1.0"
    environment: Literal["development", "staging", "production", "test"] = "development"
    debug: bool = False

    # ----- API -----
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = True
    api_key: str = "change-me-in-production"
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    # ----- LLM -----
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    ollama_base_url: str | None = None
    llm_model: str = "gpt-4o-mini"
    llm_temperature: float = 0.7
    llm_max_tokens: int = 4096

    # ----- Database -----
    database_url: str = "sqlite+aiosqlite:///./nexus.db"

    # ----- Vector store -----
    chroma_persist_dir: str = "./chroma"

    # ----- Tool APIs -----
    tavily_api_key: str | None = None

    # ----- Logging -----
    log_level: str = "INFO"
    log_format: Literal["json", "console"] = "console"

    # ----- Sandbox -----
    code_exec_timeout_seconds: int = 10
    code_exec_max_output_bytes: int = 10000

    # ----- Agent -----
    max_agent_iterations: int = 10
    enable_memory: bool = True

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_cors_origins(cls, v: str | list[str]) -> list[str]:
        """Allow CORS_ORIGINS to be passed as comma-separated string."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @field_validator("environment", mode="before")
    @classmethod
    def detect_environment(cls, v: str | None) -> str:
        if v:
            return v
        import os

        return os.getenv("ENVIRONMENT", "development")


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance — read once at startup."""
    return Settings()
