from __future__ import annotations

from typing import Any

from PIL import Image

from .classify_node import is_valid_artwork_and_room
from .client import GeminiClient
from .config import VisualizerConfig
from .pipeline_langgraph import VizState
from .pipeline_sequential import _load_image
from .runner import _save_image


def load_preview_images(room_path: str, art_path: str) -> tuple[Image.Image, Image.Image]:
    return _load_image(room_path), _load_image(art_path)


def run_preview_with_graph(
    cfg: VisualizerConfig,
    room_img: Image.Image,
    art_img: Image.Image,
    upload_image_url: str | None,
    visualizer_client: GeminiClient,
    visualizer_graph: Any,
) -> str:
    valid, is_artwork, is_room = is_valid_artwork_and_room(art_img, room_img)
    if not valid:
        if not is_artwork and not is_room:
            raise ValueError(
                "First image is not recognized as an artwork and second image is not recognized as a room."
            )
        if not is_artwork:
            raise ValueError("First image is not recognized as an artwork.")
        if not is_room:
            raise ValueError("Second image is not recognized as a room.")

    state: VizState = {
        "cfg": cfg,
        "client": visualizer_client,
        "room_img": room_img,
        "art_img": art_img,
        "used_enhancement": False,
        "retries_used": 0,
    }
    result = visualizer_graph.invoke(state)
    _save_image(result["out_img"], upload_image_url)

    return result["appraisal"].summary
