from __future__ import annotations

from enum import Enum


class JobStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class ArtworkType(str, Enum):
    PAINTING = "painting"
    SCULPTURE = "sculpture"
    NOT_ARTWORK = "not_artwork"


_NOT_ARTWORK_ALIASES = {
    "not_artwork",
    "not an artwork",
    "not_an_artwork",
    "not-artwork",
    "not art",
}


def normalize_artwork_type(value: str | None) -> str:
    normalized = (value or "").strip().lower().replace("-", "_")
    if normalized in _NOT_ARTWORK_ALIASES:
        return ArtworkType.NOT_ARTWORK.value
    if normalized in {ArtworkType.PAINTING.value, ArtworkType.SCULPTURE.value}:
        return normalized
    return normalized
