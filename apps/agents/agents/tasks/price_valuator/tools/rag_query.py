"""RAG query tool for finding comparable artworks."""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from agents.providers.rag.settings import EnvSettings, load_config
from agents.providers.rag.pinecone_store import build_pinecone_client, get_index, index_name
from agents.providers.rag.embedder.openai_embed import OpenAITextEmbedder
from agents.providers.rag.context.canonicalize import canonicalize_feature_state

logger = logging.getLogger(__name__)


class RAGQueryTool:
    """Tool for querying Pinecone for comparable artworks."""

    def __init__(self, config_path: str = None):
        self.cfg = load_config(config_path)
        self.env = EnvSettings()
        self.mode = self.cfg.embedding_mode

        if self.mode != "feature_text":
            raise ValueError(f"RAG query tool requires feature_text mode, got {self.mode}")

        # Setup text embedder
        o = self.cfg.get("feature_text", "openai_embeddings", default={})
        self.text_embedder = OpenAITextEmbedder(
            api_key=self.env.OPENAI_API_KEY,
            base_url=self.env.OPENAI_BASE_URL,
            model=o.get("model", "text-embedding-3-small"),
            dimensions=o.get("dimensions", 768),
            encoding_format=o.get("encoding_format", "float"),
        )

        # Setup Pinecone
        self.pc = build_pinecone_client(self.env.PINECONE_API_KEY)
        self.prefix = self.cfg.get("pinecone", "index_prefix", default="artium")

        # Get notes config for canonicalization
        notes_cfg = self.cfg.get("feature_text", "notes", default={})
        self.strip_urls = bool(notes_cfg.get("strip_urls", True))
        self.max_total = int(notes_cfg.get("max_chars_total", 2000))
        self.max_section = int(notes_cfg.get("max_chars_per_section", 500))

    def search_comparables(
        self,
        feature_state: Dict[str, Any],
        artwork_type: str,
        top_k: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Search for comparable artworks using agents.providers.rag.

        Args:
            feature_state: Feature state from feature extractor
            artwork_type: "painting" or "sculpture"
            top_k: Number of comparables to retrieve

        Returns:
            List of comparable artworks with metadata and prices
        """
        logger.info(f"Searching for {top_k} comparable {artwork_type}s")

        # Canonicalize features to text
        schema_version = (
            self.cfg.get("feature_text", "schema_version_painting")
            if artwork_type == "painting"
            else self.cfg.get("feature_text", "schema_version_sculpture")
        )

        canon_text, canon_json = canonicalize_feature_state(
            feature_state,
            strip_urls=self.strip_urls,
            max_chars_total=self.max_total,
            max_chars_per_section=self.max_section,
            schema_version=schema_version,
        )

        # Embed canonical text
        query_vec = self.text_embedder.embed_texts([canon_text])[0]

        # Get Pinecone index
        idx = get_index(self.pc, index_name(self.prefix, self.mode, artwork_type))

        # Search
        results = idx.query(
            vector=query_vec,
            top_k=top_k,
            include_metadata=True,
        )

        # Extract comparables
        comparables = []
        for match in results.matches:
            comp = {
                "id": match.id,
                "similarity_score": float(match.score),
                "metadata": match.metadata or {},
            }

            # Extract price if available
            meta = match.metadata or {}
            comp["price"] = self._extract_price(meta)
            comp["title"] = meta.get("title", "Unknown")
            comp["author"] = meta.get("author", "Unknown")
            comp["sale_date"] = meta.get("sale_date", "")
            comp["location"] = meta.get("location", "")
            comp["lot_number"] = meta.get("lot_number", "")
            comp["features_preview"] = meta.get("canonical_text_preview", "")

            comparables.append(comp)

        logger.info(f"Found {len(comparables)} comparables")
        return comparables

    def _extract_price(self, metadata: Dict[str, Any]) -> float:
        """Extract price from metadata."""
        # Try different price field names
        for field in ["sale_price", "price", "hammer_price", "estimate_high"]:
            if field in metadata:
                try:
                    return float(metadata[field])
                except (ValueError, TypeError):
                    continue

        # If no price found, return 0 (will be filtered out later)
        return 0.0
