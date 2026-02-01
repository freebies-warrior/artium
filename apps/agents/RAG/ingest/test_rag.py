#!/usr/bin/env python
"""
Simple CLI to test RAG retrieval capability.

Usage:
    python -m apps.agents.RAG.ingest.test_rag --query "oil painting landscape" --artwork-type painting
    python -m apps.agents.RAG.ingest.test_rag --query "bronze sculpture abstract" --artwork-type sculpture
    python -m apps.agents.RAG.ingest.test_rag --query-image /path/to/image.jpg --artwork-type painting
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Optional

from apps.agents.RAG.settings import EnvSettings, load_config
from apps.agents.RAG.utils.logging import setup_logging
from apps.agents.RAG.pinecone_store import build_pinecone_client, get_index, index_name
from apps.agents.RAG.embedder.openai_embed import OpenAITextEmbedder
from apps.agents.RAG.embedder.clip_image import ClipImageEmbedder

logger = logging.getLogger(__name__)


def test_text_query(query: str, artwork_type: str, top_k: int = 5, config: Optional[str] = None) -> None:
    """Test text-based RAG query."""
    cfg = load_config(config)
    env = EnvSettings()
    mode = cfg.embedding_mode

    if mode != "feature_text":
        raise ValueError(f"Text query test requires feature_text mode, but got {mode}")

    logger.info(f"Testing text query: '{query}' for {artwork_type}s")

    # Setup embedder
    o = cfg.get("feature_text", "openai_embeddings", default={})
    text_embedder = OpenAITextEmbedder(
        api_key=env.OPENAI_API_KEY,
        base_url=env.OPENAI_BASE_URL,
        model=o.get("model", "text-embedding-3-small"),
        dimensions=o.get("dimensions", 768),
        encoding_format=o.get("encoding_format", "float"),
    )

    # Get Pinecone index
    pc = build_pinecone_client(env.PINECONE_API_KEY)
    prefix = cfg.get("pinecone", "index_prefix", default="artium")
    idx = get_index(pc, index_name(prefix, mode, artwork_type))

    # Embed query
    query_vec = text_embedder.embed_texts([query])[0]

    # Search
    results = idx.query(
        vector=query_vec,
        top_k=top_k,
        include_metadata=True,
    )

    # Display results
    print(f"\n{'='*80}")
    print(f"Query: '{query}'")
    print(f"Artwork Type: {artwork_type}")
    print(f"Results: {len(results.matches)} matches found")
    print(f"{'='*80}\n")

    for i, match in enumerate(results.matches, 1):
        print(f"Result {i}: Score={match.score:.4f}")
        print(f"  ID: {match.id}")
        if match.metadata:
            # Print relevant metadata
            for key in ["title", "author", "sale_date", "sale_title", "location", "lot_number"]:
                if key in match.metadata:
                    print(f"  {key}: {match.metadata[key]}")
            # Show canonical preview if available
            if "canonical_text_preview" in match.metadata:
                preview = match.metadata["canonical_text_preview"]
                print(f"  features: {preview}")
        print()


def test_image_query(image_path: str, artwork_type: str, top_k: int = 5, config: Optional[str] = None) -> None:
    """Test image-based RAG query."""
    cfg = load_config(config)
    env = EnvSettings()
    mode = cfg.embedding_mode

    if mode != "image":
        raise ValueError(f"Image query test requires image mode, but got {mode}")

    logger.info(f"Testing image query: '{image_path}' for {artwork_type}s")

    # Setup embedder
    clip_cfg = cfg.get("image", "clip", default={})
    image_embedder = ClipImageEmbedder(
        model_name=clip_cfg.get("model", "clip-ViT-B-32"),
        device=clip_cfg.get("device", "cpu"),
    )

    # Load and embed image
    image_bytes = Path(image_path).read_bytes()
    query_vec = image_embedder.embed_image(image_bytes)

    # Get Pinecone index
    pc = build_pinecone_client(env.PINECONE_API_KEY)
    prefix = cfg.get("pinecone", "index_prefix", default="artium")
    idx = get_index(pc, index_name(prefix, mode, artwork_type))

    # Search
    results = idx.query(
        vector=query_vec,
        top_k=top_k,
        include_metadata=True,
    )

    # Display results
    print(f"\n{'='*80}")
    print(f"Query Image: {image_path}")
    print(f"Artwork Type: {artwork_type}")
    print(f"Results: {len(results.matches)} matches found")
    print(f"{'='*80}\n")

    for i, match in enumerate(results.matches, 1):
        print(f"Result {i}: Score={match.score:.4f}")
        print(f"  ID: {match.id}")
        if match.metadata:
            for key in ["title", "author", "sale_date", "sale_title", "location", "lot_number"]:
                if key in match.metadata:
                    print(f"  {key}: {match.metadata[key]}")
        print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Test RAG retrieval capability"
    )
    parser.add_argument("--config", default=None, help="Path to config.yaml")
    parser.add_argument("--top-k", type=int, default=5, help="Number of results to retrieve")

    # Query options
    parser.add_argument("--query", default=None, help="Text query for retrieval")
    parser.add_argument("--query-image", default=None, help="Image path for image-based retrieval")

    # Artwork type
    parser.add_argument(
        "--artwork-type",
        choices=["painting", "sculpture"],
        required=True,
        help="Type of artwork to query",
    )

    args = parser.parse_args()

    if not args.query and not args.query_image:
        parser.error("Either --query or --query-image must be provided")

    if args.query:
        test_text_query(args.query, args.artwork_type, top_k=args.top_k, config=args.config)
    else:
        test_image_query(args.query_image, args.artwork_type, top_k=args.top_k, config=args.config)


if __name__ == "__main__":
    setup_logging()
    main()
