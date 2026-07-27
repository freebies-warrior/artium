from __future__ import annotations

import json
import logging
from typing import Any, Callable, Dict, List

from langgraph.types import Command

from .types import FeatureState, MarketFeatures

logger = logging.getLogger(__name__)


def _make_queries(author: str) -> List[str]:
    return [
        f"{author} museum exhibition",
        f"{author} biennale exhibition",
        f"{author} Sotheby's auction results",
        f"{author} Christie's auction results",
        f"{author} recent review trending",
    ]


def market_intelligence_node(
    search_fn: Callable[[str, int], List[Dict[str, str]]],
    max_results_per_query: int = 3,
):
    def _node(state: FeatureState) -> Command:
        try:
            md = state["metadata"]
            author = md.get("author", "").strip()
            if not author:
                raise ValueError("Missing metadata.author")

            sources: List[Dict[str, str]] = []
            for q in _make_queries(author):
                sources.extend(search_fn(q, max_results_per_query))

            # Lightweight heuristic summarization (you can replace with an LLM later)
            institutional = {
                "signal_count": sum(
                    1
                    for s in sources
                    if "museum" in (s.get("snippet", "").lower() + s.get("title", "").lower())
                ),
                "notes": "Counts are heuristic; replace with structured parsing for precision.",
            }
            auction_velocity = {
                "signal_count": sum(
                    1
                    for s in sources
                    if "sotheby" in (s.get("snippet", "").lower() + s.get("title", "").lower())
                    or "christie" in (s.get("snippet", "").lower() + s.get("title", "").lower())
                ),
                "notes": "Heuristic hit-count for major houses; add dedicated auction dataset for accuracy.",
            }
            sentiment = {
                "signal_count": sum(
                    1
                    for s in sources
                    if "trend" in (s.get("snippet", "").lower() + s.get("title", "").lower())
                    or "review" in (s.get("snippet", "").lower() + s.get("title", "").lower())
                ),
                "notes": "Heuristic press/trend hit-count; add time-bounded queries for recency.",
            }

            mf = MarketFeatures(
                institutional_standing=institutional,
                auction_velocity=auction_velocity,
                sentiment_hype=sentiment,
                sources=sources,
            ).model_dump()

            logger.info("Market features extracted.")
            return Command(update={"market_features": mf}, goto="state_coordinator")

        except Exception as e:
            logger.error("Market agent failed", extra={"error_type": type(e).__name__})
            errs = list(state.get("errors", []))
            errs.append(f"market_agent_error: {e}")
            return Command(update={"errors": errs}, goto="state_coordinator")

    return _node
