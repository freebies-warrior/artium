from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from agents.core.settings import Settings, get_settings


def EnvSettings() -> Settings:
    """Backward-compatible constructor used by existing RAG modules."""
    return get_settings()


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
        config_path = get_settings().VECTORDB_CONFIG
    p = Path(config_path)
    data = yaml.safe_load(p.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Config at {p} must be a YAML dict")
    return AppConfig(raw=data, path=p)
