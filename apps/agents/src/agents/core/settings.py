from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import TypeVar

from pydantic_settings import BaseSettings, SettingsConfigDict

from agents.core.constants import DEFAULT_GEMINI_IMAGE_MODEL, DEFAULT_GEMINI_TEXT_MODEL


def _resolve_agents_root() -> Path:
    package_root = Path(__file__).resolve().parent.parent
    for directory in package_root.parents:
        if (directory / "pyproject.toml").exists():
            return directory
    return package_root


AGENTS_ROOT = _resolve_agents_root()
ENV_FILE = AGENTS_ROOT / ".env"
_E = TypeVar("_E", bound=Exception)


class Settings(BaseSettings):
    """Centralized settings for the agents codebase."""

    model_config = SettingsConfigDict(
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Internal agents service configuration
    INTERNAL_TOKEN: str = ""
    BACKEND_URL: str = "http://localhost:8080"

    # Visualizer configuration
    VISUALIZER_GEMINI_MODEL: str = DEFAULT_GEMINI_IMAGE_MODEL
    VISUALIZER_GEMINI_TEXT_MODEL: str = DEFAULT_GEMINI_TEXT_MODEL
    VISUALIZER_MAX_RETRIES: int = 1
    VISUALIZER_ENHANCE_IF_LOW_QUALITY: bool = True
    VISUALIZER_USE_LANGGRAPH: bool = True

    # RAG configuration
    VECTORDB_CONFIG: str = "src/agents/providers/rag/config.yaml"
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

    def _require(
        self,
        name: str,
        value: str | None,
        *,
        error_type: type[_E] = ValueError,
    ) -> str:
        normalized = (value or "").strip()
        if normalized:
            return normalized
        raise error_type(
            f"{name} is not configured. Set `{name}` in environment or in `{ENV_FILE}`."
        )

    def require_internal_token(self) -> str:
        return self._require("INTERNAL_TOKEN", self.INTERNAL_TOKEN)

    def require_google_api_key(self) -> str:
        return self._require("GOOGLE_API_KEY", self.GOOGLE_API_KEY)

    def require_openai_api_key(self) -> str:
        return self._require("OPENAI_API_KEY", self.OPENAI_API_KEY)

    def require_serpapi_api_key(self) -> str:
        return self._require("SERPAPI_API_KEY", self.SERPAPI_API_KEY)

    def require_pinecone_api_key(self) -> str:
        return self._require("PINECONE_API_KEY", self.PINECONE_API_KEY)

    def require_manus_api_key(self) -> str:
        return self._require("MANUS_API_KEY", self.MANUS_API_KEY)


@lru_cache
def get_settings() -> Settings:
    return Settings(_env_file=ENV_FILE)
