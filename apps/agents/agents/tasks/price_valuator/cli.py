#!/usr/bin/env python
"""
CLI to test price valuation for artworks.

Usage:
    python -m agents.tasks.price_valuator.cli --image-url https://example.com/artwork.jpg --artwork-type painting
    python -m agents.tasks.price_valuator.cli --image-url https://example.com/sculpture.jpg --artwork-type sculpture
"""

from __future__ import annotations

import argparse
import json
import logging
import sys

from agents.core.logging import configure_logging
from agents.core.settings import get_settings

from agents.tasks.feature_extractor.tools.image_tool import fetch_and_standardize_image
from agents.tasks.feature_extractor.types import ArtworkMetadata, FeatureState
from agents.tasks.feature_extractor.graph import build_graph
from agents.tasks.feature_extractor.llm_client import GeminiVisionClient
from agents.tasks.price_valuator.graph import build_valuation_graph
from agents.tasks.price_valuator.types import ValuationState

logger = logging.getLogger(__name__)


def main():
    configure_logging(get_settings().LOG_LEVEL)

    parser = argparse.ArgumentParser(description="Test price valuation for artwork")
    parser.add_argument("--image-url", required=True, help="URL of artwork image")
    parser.add_argument("--title", default="Unknown", help="Artwork title")
    parser.add_argument("--author", default="Unknown", help="Artist name")
    parser.add_argument("--year", default=None, help="Year created")
    parser.add_argument("--medium-hint", default=None, help="Medium hint")
    parser.add_argument(
        "--artwork-type",
        choices=["painting", "sculpture"],
        default=None,
        help="Artwork type (if known)",
    )
    parser.add_argument("--config", default=None, help="Path to RAG config.yaml")
    parser.add_argument("--out", default=None, help="Output file for full results (JSON)")
    args = parser.parse_args()

    # Step 1: Fetch and prepare image
    logger.info("Fetching image...")
    image_bytes, image_mode, image_size = fetch_and_standardize_image(
        args.image_url, target_size=(1024, 1024)
    )

    # Step 2: Extract features (if artwork_type not provided, classifier will determine it)
    logger.info("Extracting features...")
    metadata = ArtworkMetadata(
        title=args.title,
        author=args.author,
        year=args.year,
        medium_hint=args.medium_hint,
    ).model_dump()

    initial_state: FeatureState = {
        "metadata": metadata,
        "image_bytes": image_bytes,
        "image_mode": image_mode,
        "image_size": image_size,
        "errors": [],
    }

    feature_graph = build_graph(vision_llm=GeminiVisionClient())
    feature_result = feature_graph.invoke(initial_state)

    artwork_type = feature_result.get("artwork_type", "").lower()
    if artwork_type not in ("painting", "sculpture"):
        logger.error(f"Invalid artwork type determined: {artwork_type}")
        sys.exit(1)

    logger.info(f"Artwork classified as: {artwork_type}")

    # Step 3: Run valuation
    logger.info("Running price valuation...")
    valuation_state: ValuationState = {
        "artwork_features": feature_result,
        "metadata": metadata,
        "artwork_type": artwork_type,
        "image_bytes": image_bytes,
        "errors": [],
    }

    valuation_graph = build_valuation_graph(config_path=args.config)
    valuation_result = valuation_graph.invoke(valuation_state)

    # Step 4: Display results
    report = valuation_result.get("coordinator_report") or valuation_result.get(
        "justification", "No report available"
    )
    logger.info("valuation report\n%s", "=" * 80)
    logger.info("%s", report)
    logger.info("%s", "=" * 80)

    # Optional: Save full results to file
    if args.out:
        output = {
            "artwork_type": artwork_type,
            "metadata": metadata,
            "price_range": valuation_result.get("price_range", {}),
            "coordinator_report": valuation_result.get("coordinator_report", ""),
            "reasoning_steps": valuation_result.get("reasoning_steps", []),
            "comparables": [
                {
                    "title": c.get("title"),
                    "author": c.get("author"),
                    "price": c.get("price"),
                    "similarity": c.get("similarity_score"),
                }
                for c in valuation_result.get("comparables", [])[:5]
            ],
            "market_insights": valuation_result.get("market_insights", {}),
            "confidence_factors": valuation_result.get("confidence_factors", {}),
        }

        with open(args.out, "w") as f:
            json.dump(output, f, indent=2)
        logger.info(f"Full results saved to {args.out}")


if __name__ == "__main__":
    main()
