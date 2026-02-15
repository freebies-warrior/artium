"""Metadata research node for artist and historical background analysis."""

from __future__ import annotations

import logging
from langgraph.types import Command

from ..types import ValuationState
from ..llm_client import ValuationLLMClient

logger = logging.getLogger(__name__)


def metadata_research_node():
    """Create metadata research node that analyzes artist/year background."""

    def _node(state: ValuationState) -> Command:
        try:
            artwork_features = state.get("artwork_features", {})
            artwork_type = state.get("artwork_type", "artwork")
            market_insights = state.get("market_insights", {})

            # Extract available metadata
            author = artwork_features.get("author", "")
            year_created = artwork_features.get("year_created", "")
            title = artwork_features.get("title", "")

            metadata_research = {
                "author": author,
                "year_created": year_created,
                "artist_background": "",
                "historical_period": "",
                "artist_market_level": "",
                "estimated_price_impact": "",
                "research_notes": [],
            }

            # If we have author info, research the artist
            if author and author.strip() and author.lower() != "unknown":
                llm_client = ValuationLLMClient()
                artist_research = llm_client.research_artist(
                    author=author,
                    year_created=year_created,
                    artwork_type=artwork_type,
                    title=title,
                    market_insights=market_insights,
                )

                metadata_research.update(artist_research)
                logger.info(f"Artist research completed for {author}")

            else:
                metadata_research["research_notes"].append(
                    "No author information available for historical research"
                )
                logger.info("No author metadata available for research")

            # Analyze historical period if year available
            if year_created:
                try:
                    year_int = int(year_created)
                    metadata_research["historical_period"] = _determine_historical_period(year_int)
                except (ValueError, TypeError):
                    metadata_research["research_notes"].append(
                        f"Unable to parse year_created: {year_created}"
                    )

            logger.info(
                f"Metadata research complete: {metadata_research.get('artist_market_level', 'N/A')}"
            )

            return Command(
                update={
                    "metadata_research": metadata_research,
                },
                goto="price_calculation",
            )

        except Exception as e:
            logger.exception(f"Metadata research failed: {e}")
            return Command(
                update={
                    "metadata_research": {
                        "artist_background": "",
                        "historical_period": "",
                        "artist_market_level": "",
                        "estimated_price_impact": "",
                        "research_notes": [f"Metadata research error: {e}"],
                    }
                },
                goto="price_calculation",
            )

    return _node


def _determine_historical_period(year: int) -> str:
    """Determine historical period from year created."""

    if year < 1400:
        return "Medieval"
    elif year < 1600:
        return "Renaissance"
    elif year < 1750:
        return "Baroque"
    elif year < 1820:
        return "Rococo/Neoclassical"
    elif year < 1900:
        return "Romantic/Victorian"
    elif year < 1920:
        return "Late 19th/Early 20th Century"
    elif year < 1945:
        return "Modernist (Early 20th Century)"
    elif year < 1970:
        return "Post-War (Mid 20th Century)"
    elif year < 2000:
        return "Contemporary (Late 20th Century)"
    else:
        return "Modern/Contemporary (21st Century)"
