"""RAG search node for finding comparable artworks."""

from __future__ import annotations

import logging
from langgraph.types import Command

from agents.core.types import ArtworkType, normalize_artwork_type

from ..types import ValuationState
from ..tools.rag_query import RAGQueryTool

logger = logging.getLogger(__name__)


def rag_search_node(rag_tool: RAGQueryTool):
    """Create RAG search node."""

    def _node(state: ValuationState) -> Command:
        try:
            artwork_type = normalize_artwork_type(state.get("artwork_type", ""))
            if artwork_type not in (ArtworkType.PAINTING.value, ArtworkType.SCULPTURE.value):
                raise ValueError(f"Invalid artwork_type: {artwork_type}")

            # Construct feature state for RAG query
            feature_state = {
                "artwork_type": artwork_type,
                "metadata": state.get("metadata", {}),
                "vision_features": state.get("artwork_features", {}).get("vision_features", {}),
            }

            # Search for comparables
            logger.info("Searching for comparable %ss...", artwork_type)
            comparables = rag_tool.search_comparables(
                feature_state=feature_state,
                artwork_type=artwork_type,
                top_k=15,  # Get more to filter later
            )

            # Keep only whole-dollar SGD comparables in the valuation pipeline.
            priced_comparables = [c for c in comparables if c.get("price", 0) > 0]
            comparables_with_prices = [
                c
                for c in priced_comparables
                if str(c.get("currency", "SGD")).upper() == "SGD"
            ]
            skipped_non_sgd = len(priced_comparables) - len(comparables_with_prices)

            if skipped_non_sgd:
                logger.warning("Skipping %d comparables with non-SGD currency", skipped_non_sgd)

            if not comparables_with_prices:
                logger.warning("No comparables with SGD prices found")
                return Command(
                    update={
                        "comparables": [],
                        "rag_search_summary": "No comparable artworks with SGD prices found in database.",
                        "errors": ["No comparable artworks with SGD prices found"],
                    },
                    goto="END",
                )

            summary = (
                f"Found {len(comparables_with_prices)} comparable {artwork_type}s with prices. "
                f"Average similarity score: {sum(c['similarity_score'] for c in comparables_with_prices) / len(comparables_with_prices):.3f}"
            )

            logger.info(summary)
            return Command(
                update={
                    "comparables": comparables_with_prices,
                    "rag_search_summary": summary,
                },
                goto="market_analysis",
            )

        except Exception as exc:
            logger.error("RAG search failed", extra={"error_type": type(exc).__name__})
            return Command(
                update={"errors": ["RAG search error"]},
                goto="END",
            )

    return _node
