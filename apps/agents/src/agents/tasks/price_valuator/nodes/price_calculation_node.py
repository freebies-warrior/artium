"""Price calculation node for estimating artwork value with LLM reasoning."""

from __future__ import annotations

import logging
import statistics
from langgraph.types import Command

from ..types import ValuationState
from ..llm_client import ValuationLLMClient

logger = logging.getLogger(__name__)


def _to_sgd_dollars(value: float) -> int:
    """Round a numeric amount to whole SGD dollars."""

    return int(float(value) + 0.5)


def price_calculation_node():
    """Create price calculation node with LLM-powered estimation."""

    def _node(state: ValuationState) -> Command:
        try:
            comparables = state.get("comparables", [])
            market_insights = state.get("market_insights", {})

            if not comparables or not market_insights:
                return Command(
                    update={"errors": ["Missing data for price calculation"]},
                    goto="END",
                )

            # Extract prices and weights by similarity
            weighted_prices = []
            for comp in comparables:
                price = comp.get("price", 0)
                similarity = comp.get("similarity_score", 0)
                if price > 0 and similarity > 0:
                    # Weight by similarity score
                    weighted_prices.append((price, similarity))

            if not weighted_prices:
                return Command(
                    update={"errors": ["No valid prices for calculation"]},
                    goto="END",
                )

            # Calculate weighted average
            total_weight = sum(w for _, w in weighted_prices)
            weighted_avg = sum(p * w for p, w in weighted_prices) / total_weight

            # Use market insights
            median_price = market_insights.get("median_price", weighted_avg)
            price_std = market_insights.get("price_std", 0)

            # Calculate mid-point estimate (blend weighted avg and median)
            mid_estimate = (weighted_avg * 0.6) + (median_price * 0.4)

            # Try LLM-based price estimation first
            try:
                llm_client = ValuationLLMClient()
                artwork_features = state.get("artwork_features", {})
                comparables_analysis = state.get("comparables_analysis", {})

                comparable_prices = [
                    c.get("price", 0) for c in comparables if c.get("price", 0) > 0
                ]

                llm_estimate = llm_client.estimate_price_range(
                    artwork_features=artwork_features,
                    comparables_analysis=comparables_analysis,
                    market_insights=market_insights,
                    comparable_prices=comparable_prices,
                )

                low_estimate = llm_estimate.get("price_low", mid_estimate * 0.85)
                high_estimate = llm_estimate.get("price_high", mid_estimate * 1.15)

                price_range = {
                    "low": _to_sgd_dollars(llm_estimate.get("price_low", low_estimate)),
                    "mid": _to_sgd_dollars(llm_estimate.get("price_mid", mid_estimate)),
                    "high": _to_sgd_dollars(llm_estimate.get("price_high", high_estimate)),
                }

                llm_reasoning = llm_estimate.get("reasoning", "LLM-based estimate")

                logger.info(
                    f"LLM price estimate: SGD {price_range['low']:,} - SGD {price_range['mid']:,} - SGD {price_range['high']:,}"
                )

                # Build reasoning steps with LLM insights
                reasoning_steps = [
                    f"Analyzed {len(comparables)} comparable artworks using LLM reasoning",
                    f"Weighted average price: SGD {weighted_avg:,.0f} (based on similarity scores)",
                    f"Market median price: SGD {median_price:,.0f}",
                    f"LLM-enhanced estimate: {llm_reasoning}",
                ]

            except Exception as llm_error:
                logger.warning(
                    "LLM price estimation failed, using fallback",
                    extra={"error_type": type(llm_error).__name__},
                )

                # Fallback: Calculate range based on standard deviation and market variance
                cv = price_std / mid_estimate if mid_estimate > 0 else 0.2
                range_factor = max(0.15, min(0.35, cv))

                low_estimate = mid_estimate * (1 - range_factor)
                high_estimate = mid_estimate * (1 + range_factor)

                price_range = {
                    "low": _to_sgd_dollars(low_estimate),
                    "mid": _to_sgd_dollars(mid_estimate),
                    "high": _to_sgd_dollars(high_estimate),
                }

                logger.info(
                    f"Fallback price estimate: SGD {price_range['low']:,} - SGD {price_range['mid']:,} - SGD {price_range['high']:,}"
                )

                reasoning_steps = [
                    f"Analyzed {len(comparables)} comparable artworks",
                    f"Weighted average price: SGD {weighted_avg:,.0f} (based on similarity scores)",
                    f"Market median price: SGD {median_price:,.0f}",
                    f"Calculated mid-point estimate: SGD {mid_estimate:,.0f}",
                    f"Price range: SGD {low_estimate:,.0f} - SGD {high_estimate:,.0f} (±{range_factor * 100:.0f}%)",
                ]

            return Command(
                update={
                    "price_range": price_range,
                    "currency": "SGD",
                    "reasoning_steps": reasoning_steps,
                },
                goto="state_coordinator",
            )

        except Exception as e:
            logger.error("Price calculation failed", extra={"error_type": type(e).__name__})
            return Command(
                update={"errors": [f"Price calculation error: {e}"]},
                goto="END",
            )

    return _node
