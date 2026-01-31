from __future__ import annotations

import os
from dotenv import load_dotenv
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()

class EnvSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Pinecone
    PINECONE_API_KEY: str

    # OpenAI
    OPENAI_API_KEY: str
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"

    # Manus (optional)
    MANUS_API_KEY: Optional[str] = None

    # Service
    APP_ENV: str = "dev"
    LOG_LEVEL: str = "INFO"


@dataclass(frozen=True)
class AppConfig:
    raw: Dict[str, Any]
    path: Path

    @property
    def embedding_mode(self) -> str:
        return str(self.raw.get("embedding_mode", "feature_text"))

    def get(self, *keys: str, default: Any = None) -> Any:
        cur: Any = self.raw
        for k in keys:
            if not isinstance(cur, dict) or k not in cur:
                return default
            cur = cur[k]
        return cur


def load_config(config_path: str | os.PathLike = None) -> AppConfig:
    if config_path is None:
        config_path = os.getenv("VECTORDB_CONFIG", "apps/agents/RAG/config.yaml")
    p = Path(config_path)
    data = yaml.safe_load(p.read_text(encoding="utf-8"))
    if not isinstance(data, dict): 
        raise ValueError(f"Config at {p} must be a YAML dict")
    return AppConfig(raw=data, path=p)
