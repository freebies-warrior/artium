from __future__ import annotations

import argparse
import json
import logging

from agents.core.logging import configure_logging
from agents.core.settings import get_settings

from .graph import build_graph
from .llm_client import GeminiVisionClient
from .tools.image_tool import fetch_and_standardize_image
from .types import ArtworkMetadata, FeatureState

logger = logging.getLogger(__name__)


def parse_args():
    p = argparse.ArgumentParser(
        description="Unified feature extraction for paintings and sculptures (vision + market)."
    )
    p.add_argument("--title", default="Unknown")
    p.add_argument("--author", default="Unknown")
    p.add_argument("--year", default=None)
    p.add_argument("--image-url", required=True)
    p.add_argument("--medium-hint", default=None)
    p.add_argument("--out", default="features.json")
    return p.parse_args()


def main():
    configure_logging(get_settings().LOG_LEVEL)
    args = parse_args()

    md = ArtworkMetadata(
        title=args.title,
        author=args.author,
        year=args.year,
        medium_hint=args.medium_hint,
    ).model_dump()

    image_bytes, image_mode, image_size = fetch_and_standardize_image(
        args.image_url, target_size=(1024, 1024)
    )

    initial_state: FeatureState = {
        "metadata": md,
        "image_bytes": image_bytes,
        "image_mode": image_mode,
        "image_size": image_size,
        "errors": [],
    }

    graph = build_graph(vision_llm=GeminiVisionClient())
    final = graph.invoke(initial_state)

    # Remove image_bytes before writing to JSON (binary data not JSON-serializable)
    output = {k: v for k, v in final.items() if k != "image_bytes"}

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    logger.info("Wrote %s", args.out)


if __name__ == "__main__":
    main()
