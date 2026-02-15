"""RAG search node for finding comparable artworks."""

from __future__ import annotations

import logging
from langgraph.types import Command

from ..types import ValuationState
from ..tools.rag_query import RAGQueryTool

logger = logging.getLogger(__name__)


def rag_search_node(rag_tool: RAGQueryTool):
    """Create RAG search node."""

    def _node(state: ValuationState) -> Command:
        try:
            artwork_type = state.get("artwork_type", "").lower()
            if artwork_type not in ("painting", "sculpture"):
                raise ValueError(f"Invalid artwork_type: {artwork_type}")

            # Construct feature state for RAG query
            feature_state = {
                "artwork_type": artwork_type,
                "metadata": state.get("metadata", {}),
                "vision_features": state.get("artwork_features", {}).get("vision_features", {}),
            }

            # Search for comparables
            logger.info(f"Searching for comparable {artwork_type}s...")
            comparables = rag_tool.search_comparables(
                feature_state=feature_state,
                artwork_type=artwork_type,
                top_k=15,  # Get more to filter later
            )

            # Filter out items without prices
            comparables_with_prices = [c for c in comparables if c.get("price", 0) > 0]

            if not comparables_with_prices:
                logger.warning("No comparables with prices found")
                return Command(
                    update={
                        "comparables": [],
                        "rag_search_summary": "No comparable artworks with prices found in database.",
                        "errors": ["No comparables with prices found"],
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

        except Exception as e:
            logger.exception(f"RAG search failed: {e}")
            return Command(
                update={"errors": [f"RAG search error: {e}"]},
                goto="END",
            )

    return _node
