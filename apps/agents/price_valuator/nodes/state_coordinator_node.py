"""State coordinator node that gathers and synthesizes all analysis."""

from __future__ import annotations

import logging
from langgraph.types import Command

from ..types import ValuationState

logger = logging.getLogger(__name__)


def state_coordinator_node():
    """Create state coordinator node that gathers reports from all analysis."""

    def _node(state: ValuationState) -> Command:
        try:
            # Gather all analysis reports
            price_range = state.get("price_range", {})
            comparables = state.get("comparables", [])
            market_insights = state.get("market_insights", {})
            metadata_research = state.get("metadata_research", {})
            comparables_analysis = state.get("comparables_analysis", {})
            reasoning_steps = state.get("reasoning_steps", [])

            # Build comprehensive valuation report
            coordinator_report = _synthesize_report(
                price_range=price_range,
                comparables=comparables,
                market_insights=market_insights,
                metadata_research=metadata_research,
                comparables_analysis=comparables_analysis,
                reasoning_steps=reasoning_steps,
            )

            logger.info(
                f"State coordination complete. Final estimate: ${price_range.get('mid', 0):,.2f}"
            )

            return Command(
                update={
                    "coordinator_report": coordinator_report,
                    "final_justification": coordinator_report,
                },
                goto="END",
            )

        except Exception as e:
            logger.exception(f"State coordination failed: {e}")
            return Command(
                update={
                    "coordinator_report": f"Error during coordination: {e}",
                    "errors": state.get("errors", []) + [f"Coordination error: {e}"],
                },
                goto="END",
            )

    return _node


def _synthesize_report(
    price_range: dict,
    comparables: list,
    market_insights: dict,
    metadata_research: dict,
    comparables_analysis: dict,
    reasoning_steps: list,
) -> str:
    """Synthesize all analysis into comprehensive report."""

    report_lines = []

    # Header
    report_lines.append("=" * 70)
    report_lines.append("COMPREHENSIVE PRICE VALUATION REPORT")
    report_lines.append("=" * 70)
    report_lines.append("")

    # Price Estimate
    price_low = price_range.get("low", 0)
    price_mid = price_range.get("mid", 0)
    price_high = price_range.get("high", 0)

    report_lines.append("PRICE ESTIMATE")
    report_lines.append("-" * 70)
    report_lines.append(f"Estimated Range: ${price_low:,.2f} - ${price_high:,.2f}")
    report_lines.append(f"Most Likely Price: ${price_mid:,.2f}")
    report_lines.append("")

    # Comparable Artworks
    if comparables:
        report_lines.append("COMPARABLE ARTWORKS ANALYSIS")
        report_lines.append("-" * 70)
        report_lines.append(f"Total Comparables Found: {len(comparables)}")

        top_comps = sorted(comparables, key=lambda x: x.get("similarity_score", 0), reverse=True)[
            :5
        ]

        for i, comp in enumerate(top_comps, 1):
            report_lines.append(
                f'{i}. "{comp.get("title", "Unknown")}" by {comp.get("author", "Unknown")}'
            )
            report_lines.append(
                f"   Price: ${comp.get('price', 0):,.2f} | Similarity: {comp.get('similarity_score', 0):.1%}"
            )
        report_lines.append("")

    # LLM Comparables Analysis
    if comparables_analysis and comparables_analysis.get("key_similarities"):
        report_lines.append("KEY SIMILARITIES TO COMPARABLES")
        report_lines.append("-" * 70)
        for similarity in comparables_analysis.get("key_similarities", [])[:5]:
            report_lines.append(f"• {similarity}")
        report_lines.append("")

    # Market Insights
    if market_insights:
        report_lines.append("MARKET ANALYSIS")
        report_lines.append("-" * 70)
        report_lines.append(f"Market Average Price: ${market_insights.get('avg_price', 0):,.2f}")
        report_lines.append(f"Market Median Price: ${market_insights.get('median_price', 0):,.2f}")
        report_lines.append(
            f"Price Trend: {market_insights.get('trend_direction', 'unknown').title()}"
        )
        report_lines.append(
            f"Recent Sales: {market_insights.get('num_recent_sales', 0)} in last 12 months"
        )
        report_lines.append("")

    # Artist/Metadata Research
    if metadata_research and (
        metadata_research.get("author") or metadata_research.get("year_created")
    ):
        report_lines.append("ARTIST & HISTORICAL BACKGROUND")
        report_lines.append("-" * 70)

        if metadata_research.get("author"):
            report_lines.append(f"Artist: {metadata_research.get('author')}")

        if metadata_research.get("year_created"):
            report_lines.append(f"Year Created: {metadata_research.get('year_created')}")
            if metadata_research.get("historical_period"):
                report_lines.append(
                    f"Historical Period: {metadata_research.get('historical_period')}"
                )

        if metadata_research.get("artist_background"):
            report_lines.append(f"Artist Background: {metadata_research.get('artist_background')}")

        if metadata_research.get("artist_market_level"):
            report_lines.append(f"Market Level: {metadata_research.get('artist_market_level')}")

        if metadata_research.get("estimated_price_impact"):
            report_lines.append(f"Price Impact: {metadata_research.get('estimated_price_impact')}")

        if metadata_research.get("research_notes"):
            for note in metadata_research.get("research_notes", []):
                report_lines.append(f"Note: {note}")

        report_lines.append("")

    # Methodology
    if reasoning_steps:
        report_lines.append("VALUATION METHODOLOGY")
        report_lines.append("-" * 70)
        for i, step in enumerate(reasoning_steps, 1):
            report_lines.append(f"{i}. {step}")
        report_lines.append("")

    # Conclusion
    report_lines.append("CONCLUSION")
    report_lines.append("-" * 70)
    report_lines.append(
        f"Based on comprehensive analysis of {len(comparables)} comparable artworks, "
        f"market trends, and artist background, the estimated value of this artwork "
        f"is ${price_mid:,.2f}, with a reasonable range between ${price_low:,.2f} and ${price_high:,.2f}."
    )

    report_lines.append("")
    report_lines.append("=" * 70)

    return "\n".join(report_lines)
