"""Confidence assessment node for valuation reliability with LLM justification."""

from __future__ import annotations

import logging
import statistics
from langgraph.types import Command

from ..types import ValuationState
from ..llm_client import ValuationLLMClient

logger = logging.getLogger(__name__)


def confidence_node():
    """Create confidence assessment node with LLM-generated justification."""
    
    def _node(state: ValuationState) -> Command:
        try:
            comparables = state.get("comparables", [])
            market_insights = state.get("market_insights", {})
            price_trends = state.get("price_trends", {})
            price_range = state.get("price_range", {})
            
            if not comparables:
                return Command(
                    update={
                        "confidence_score": 0.0,
                        "justification": "Insufficient data for valuation.",
                    },
                    goto="END",
                )
            
            # Factor 1: Number of comparables (0-1)
            num_comparables = len(comparables)
            num_score = min(1.0, num_comparables / 10)  # Max at 10 comparables
            
            # Factor 2: Average similarity (0-1)
            similarities = [c.get("similarity_score", 0) for c in comparables]
            avg_similarity = statistics.mean(similarities) if similarities else 0
            similarity_score = avg_similarity
            
            # Factor 3: Price variance (lower is better, 0-1)
            cv = price_trends.get("coefficient_of_variation", 0)
            variance_score = max(0, 1 - cv)  # Lower CV = higher confidence
            
            # Factor 4: Recency (0-1)
            recency_score = price_trends.get("recency_ratio", 0.5)
            
            # Factor 5: Feature quality (based on similarity distribution)
            if len(similarities) > 1:
                sim_std = statistics.stdev(similarities)
                feature_quality = 1 - sim_std  # Lower std = more consistent matches
            else:
                feature_quality = 0.7
            
            # Calculate overall confidence (weighted average)
            confidence_score = (
                num_score * 0.25 +
                similarity_score * 0.30 +
                variance_score * 0.25 +
                recency_score * 0.10 +
                feature_quality * 0.10
            )
            
            confidence_score = max(0.0, min(1.0, confidence_score))
            
            confidence_factors = {
                "num_comparables": num_comparables,
                "avg_similarity": round(avg_similarity, 3),
                "price_variance": round(cv, 3),
                "recency_score": round(recency_score, 3),
                "feature_quality": round(feature_quality, 3),
                "num_score": round(num_score, 3),
                "similarity_score": round(similarity_score, 3),
                "variance_score": round(variance_score, 3),
            }
            
            # Use LLM to generate comprehensive professional justification
            try:
                llm_client = ValuationLLMClient()
                artwork_features = state.get("artwork_features", {})
                comparables_analysis = state.get("comparables_analysis", {})
                
                justification = llm_client.generate_justification(
                    artwork_features=artwork_features,
                    price_range=price_range,
                    comparables_analysis=comparables_analysis,
                    market_insights=insights,
                    confidence_factors=confidence_factors,
                    comparables=comparables,
                )
                
                logger.info(f"LLM justification generated (length: {len(justification)})")
                
            except Exception as llm_error:
                logger.warning(f"LLM justification failed, using fallback: {llm_error}")
                # Fallback to simple justification
                justification = _build_justification(
                    state, comparables, confidence_score, confidence_factors, market_insights
                )
            
            logger.info(f"Confidence score: {confidence_score:.3f}")
            
            return Command(
                update={
                    "confidence_score": confidence_score,
                    "confidence_factors": confidence_factors,
                    "justification": justification,
                },
                goto="END",
            )
            
        except Exception as e:
            logger.exception(f"Confidence assessment failed: {e}")
            return Command(
                update={
                    "confidence_score": 0.0,
                    "justification": f"Error in confidence assessment: {e}",
                    "errors": [f"Confidence error: {e}"],
                },
                goto="END",
            )
    
    return _node


def _build_justification(
    state: ValuationState,
    comparables: list,
    confidence: float,
    factors: dict,
    insights: dict,
) -> str:
    """Build detailed justification for the valuation."""
    
    price_range = state.get("price_range", {})
    artwork_type = state.get("artwork_type", "artwork")
    reasoning_steps = state.get("reasoning_steps", [])
    
    lines = []
    
    # Header
    lines.append(f"PRICE VALUATION FOR {artwork_type.upper()}")
    lines.append("")
    
    # Price estimate
    lines.append(f"ESTIMATED PRICE RANGE:")
    lines.append(f"  Low:  ${price_range.get('low', 0):,.2f}")
    lines.append(f"  Mid:  ${price_range.get('mid', 0):,.2f} (most likely)")
    lines.append(f"  High: ${price_range.get('high', 0):,.2f}")
    lines.append("")
    
    # Confidence
    conf_level = "HIGH" if confidence > 0.7 else "MEDIUM" if confidence > 0.4 else "LOW"
    lines.append(f"CONFIDENCE: {conf_level} ({confidence:.1%})")
    lines.append("")
    
    # Methodology
    lines.append("VALUATION METHODOLOGY:")
    for i, step in enumerate(reasoning_steps, 1):
        lines.append(f"  {i}. {step}")
    lines.append("")
    
    # Comparables summary
    lines.append("COMPARABLE ARTWORKS:")
    lines.append(f"  Found: {factors['num_comparables']} similar {artwork_type}s")
    lines.append(f"  Average similarity: {factors['avg_similarity']:.1%}")
    
    # Show top 3 comparables
    top_comps = sorted(comparables, key=lambda x: x.get("similarity_score", 0), reverse=True)[:3]
    for i, comp in enumerate(top_comps, 1):
        title = comp.get("title", "Unknown")
        author = comp.get("author", "Unknown")
        price = comp.get("price", 0)
        sim = comp.get("similarity_score", 0)
        lines.append(f"  {i}. \"{title}\" by {author} - ${price:,.2f} (similarity: {sim:.1%})")
    lines.append("")
    
    # Market insights
    lines.append("MARKET ANALYSIS:")
    lines.append(f"  Market average: ${insights.get('avg_price', 0):,.2f}")
    lines.append(f"  Market median: ${insights.get('median_price', 0):,.2f}")
    lines.append(f"  Price trend: {insights.get('trend_direction', 'unknown')}")
    lines.append(f"  Recent sales (last 12 mo): {insights.get('num_recent_sales', 0)}")
    lines.append("")
    
    # Confidence factors
    lines.append("CONFIDENCE FACTORS:")
    lines.append(f"  Data quantity: {factors['num_score']:.1%} ({factors['num_comparables']} comparables)")
    lines.append(f"  Match quality: {factors['similarity_score']:.1%}")
    lines.append(f"  Price consistency: {factors['variance_score']:.1%} (CV: {factors['price_variance']:.2f})")
    lines.append(f"  Data recency: {factors['recency_score']:.1%}")
    lines.append("")
    
    # Caveats
    if confidence < 0.7:
        lines.append("IMPORTANT NOTES:")
        if factors['num_comparables'] < 5:
            lines.append("  - Limited comparable data available")
        if factors['avg_similarity'] < 0.7:
            lines.append("  - Comparables may not be ideal matches")
        if factors['price_variance'] > 0.5:
            lines.append("  - High price variance in market")
        if factors['recency_score'] < 0.5:
            lines.append("  - Limited recent sales data")
        lines.append("  - Consider seeking additional expert appraisal")
    
    return "\n".join(lines)
