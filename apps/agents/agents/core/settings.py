from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


class Settings(BaseSettings):
    """Centralized settings for the agents codebase."""

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Internal agents service configuration
    INTERNAL_TOKEN: str = ""
    BACKEND_URL: str = "http://localhost:8080"

    # Visualizer configuration
    VISUALIZER_GEMINI_MODEL: str = "gemini-2.5-flash-image"
    VISUALIZER_GEMINI_TEXT_MODEL: str = "gemini-2.5-flash"
    VISUALIZER_MAX_RETRIES: int = 1
    VISUALIZER_ENHANCE_IF_LOW_QUALITY: bool = True
    VISUALIZER_USE_LANGGRAPH: bool = True

    # RAG configuration
    VECTORDB_CONFIG: str = "agents/providers/rag/config.yaml"
    LOG_LEVEL: str = "INFO"
    APP_ENV: str = "dev"

    # External providers
    OPENAI_API_KEY: str | None = None
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    GOOGLE_API_KEY: str | None = None
    SERPAPI_API_KEY: str | None = None
    PINECONE_API_KEY: str | None = None
    MANUS_API_KEY: str | None = None
    MANUS_BASE_URL: str = "https://api.manus.im"

    @property
    def backend_url(self) -> str:
        return self.BACKEND_URL.rstrip("/")


@lru_cache
def get_settings() -> Settings:
    return Settings()
