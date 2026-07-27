from __future__ import annotations

import argparse
import logging

from apps.agents.RAG.settings import EnvSettings, load_config
from apps.agents.RAG.pinecone_store import (
    build_pinecone_client,
    ensure_index,
    index_name,
)
from apps.agents.RAG.embedder.numeric import NumericFeatureEmbedder
from apps.agents.RAG.embedder.clip_image import ClipImageEmbedder
from apps.agents.RAG.utils.logging import setup_logging


logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=None, help="Path to config.yaml")
    args = parser.parse_args()

    cfg = load_config(args.config)
    env = EnvSettings()

    pc = build_pinecone_client(env.PINECONE_API_KEY)

    prefix = cfg.get("pinecone", "index_prefix", default="artium")
    mode = cfg.embedding_mode
    metric = cfg.get("pinecone", "metric", default="cosine")
    cloud = cfg.get("pinecone", "cloud", default="aws")
    region = cfg.get("pinecone", "region", default="us-east-1")

    if mode == "feature_text":
        dim = int(cfg.get("feature_text", "openai_embeddings", "dimensions", default=768))
        dims = {"painting": dim, "sculpture": dim}
    elif mode == "numeric":
        fmap = cfg.get("numeric", "feature_map", default={})
        emb = NumericFeatureEmbedder(feature_map=fmap)
        dims = {
            "painting": emb.dimension_for_type("painting"),
            "sculpture": emb.dimension_for_type("sculpture"),
        }
    elif mode == "image":
        clip_cfg = cfg.get("image", "clip", default={})
        emb = ClipImageEmbedder(
            model_name=clip_cfg.get("model", "clip-ViT-B-32"),
            device=clip_cfg.get("device", "cpu"),
        )
        dims = {"painting": emb.dimension, "sculpture": emb.dimension}
    else:
        raise ValueError(f"Unknown embedding_mode={mode}")

    for artwork_type in ("painting", "sculpture"):
        name = index_name(prefix, mode, artwork_type)
        ensure_index(
            pc=pc,
            name=name,
            dimension=dims[artwork_type],
            metric=metric,
            cloud=cloud,
            region=region,
        )
        logger.info("Ensured index: %s (dim=%s)", name, dims[artwork_type])

    logger.info("Done.")


if __name__ == "__main__":
    setup_logging()
    main()
