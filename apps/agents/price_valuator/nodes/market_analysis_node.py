"""Market analysis node for analyzing comparable sales with LLM reasoning."""

from __future__ import annotations

import logging
import statistics
from datetime import datetime, timedelta
from langgraph.types import Command

from ..types import ValuationState
from ..llm_client import ValuationLLMClient

logger = logging.getLogger(__name__)


def market_analysis_node():
    """Create market analysis node with LLM-powered insights."""
    
    def _node(state: ValuationState) -> Command:
        try:
            comparables = state.get("comparables", [])
            
            if not comparables:
                return Command(
                    update={"errors": ["No comparables to analyze"]},
                    goto="END",
                )
            
            prices = [c["price"] for c in comparables if c.get("price", 0) > 0]
            
            if not prices:
                return Command(
                    update={"errors": ["No valid prices in comparables"]},
                    goto="END",
                )
            
            # Calculate statistics
            avg_price = statistics.mean(prices)
            median_price = statistics.median(prices)
            price_std = statistics.stdev(prices) if len(prices) > 1 else 0
            
            # Analyze recency
            current_year = datetime.now().year
            num_recent_sales = 0
            for comp in comparables:
                sale_date = comp.get("sale_date", "")
                if sale_date:
                    try:
                        # Parse year from date string
                        if str(current_year - 1) in sale_date or str(current_year) in sale_date:
                            num_recent_sales += 1
                    except:
                        pass
            
            # Determine trend (simplified)
            # In a real system, this would analyze historical data
            if price_std / avg_price < 0.2:
                trend = "stable"
            elif num_recent_sales > len(comparables) / 2:
                trend = "rising"
            else:
                trend = "stable"
            
            market_insights = {
                "avg_price": avg_price,
                "median_price": median_price,
                "price_std": price_std,
                "num_recent_sales": num_recent_sales,
                "trend_direction": trend,
                "total_comparables": len(comparables),
                "price_range_found": {"min": min(prices), "max": max(prices)},
            }
            
            price_trends = {
                "coefficient_of_variation": price_std / avg_price if avg_price > 0 else 0,
                "recency_ratio": num_recent_sales / len(comparables) if comparables else 0,
            }
            
            # Use LLM for deep comparative analysis
            try:
                llm_client = ValuationLLMClient()
                artwork_features = state.get("artwork_features", {})
                artwork_type = state.get("artwork_type", "artwork")
                
                comparables_analysis = llm_client.analyze_comparables(
                    artwork_features=artwork_features,
                    comparables=comparables,
                    artwork_type=artwork_type,
                )
                
                logger.info(f"LLM comparables analysis: {comparables_analysis.get('market_position', 'N/A')}")
                
            except Exception as llm_error:
                logger.warning(f"LLM analysis failed: {llm_error}")
                comparables_analysis = {
                    "key_similarities": [],
                    "key_differences": [],
                    "quality_assessment": "Unable to assess (LLM unavailable)",
                    "market_position": "unknown",
                }
            
            logger.info(
                f"Market analysis: avg=${avg_price:.2f}, median=${median_price:.2f}, "
                f"std=${price_std:.2f}, trend={trend}"
            )
            
            return Command(
                update={
                    "market_insights": market_insights,
                    "price_trends": price_trends,
                    "comparables_analysis": comparables_analysis,
                },
                goto="metadata_research",
            )
            
        except Exception as e:
            logger.exception(f"Market analysis failed: {e}")
            return Command(
                update={"errors": [f"Market analysis error: {e}"]},
                goto="END",
            )
    
    return _node
