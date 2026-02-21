from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Mapping
from uuid import UUID

if TYPE_CHECKING:
    from agents.api.agent import FeatureExtractionRequest, VisualizerRequest


@dataclass(frozen=True, slots=True)
class PreviewJobCommand:
    job_id: str
    room_url: str
    art_url: str
    upload_image_url: str | None
    upload_image_key: str | None

    @classmethod
    def from_request(cls, req: "VisualizerRequest") -> "PreviewJobCommand":
        return cls(
            job_id=req.job_id,
            room_url=str(req.room_url),
            art_url=str(req.art_url),
            upload_image_url=req.upload_image_url,
            upload_image_key=req.upload_image_key,
        )


@dataclass(frozen=True, slots=True)
class FeatureExtractionJobCommand:
    item_id: UUID | None
    image_keys: tuple[str, ...]
    image_get_urls: tuple[str, ...]
    callback_url: str | None
    metadata: Mapping[str, Any]

    @classmethod
    def from_request(cls, req: "FeatureExtractionRequest") -> "FeatureExtractionJobCommand":
        callback_url = str(req.callback_url) if req.callback_url is not None else None
        return cls(
            item_id=req.item_id,
            image_keys=tuple(req.image_keys),
            image_get_urls=tuple(str(url) for url in req.image_get_urls),
            callback_url=callback_url,
            metadata=MappingProxyType(dict(req.metadata)),
        )
