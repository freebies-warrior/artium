"""LLM client for price valuation agent."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict

from feature_extractor.llm_client import VisionLLMClient

logger = logging.getLogger(__name__)


class ValuationLLMClient:
    """LLM client for price valuation reasoning."""
    
    def __init__(self, model: str = "gemini-2.5-flash"):
        self.client = VisionLLMClient(model=model)
    
    def analyze_comparables(
        self,
        artwork_features: Dict[str, Any],
        comparables: list,
        artwork_type: str,
    ) -> Dict[str, Any]:
        """Use LLM to analyze comparable artworks and provide insights."""
        
        prompt = self._build_comparables_prompt(artwork_features, comparables, artwork_type)
        
        try:
            response = self.client.generate_json(prompt=prompt)
            return response
        except Exception as e:
            logger.error(f"LLM comparables analysis failed: {e}")
            return {
                "key_similarities": [],
                "key_differences": [],
                "quality_assessment": "Unable to assess",
                "market_position": "unknown",
            }
    
    def estimate_price_range(
        self,
        artwork_features: Dict[str, Any],
        comparables_analysis: Dict[str, Any],
        market_insights: Dict[str, Any],
        comparable_prices: list,
    ) -> Dict[str, Any]:
        """Use LLM to estimate price range with reasoning."""
        
        prompt = self._build_pricing_prompt(
            artwork_features, comparables_analysis, market_insights, comparable_prices
        )
        
        try:
            response = self.client.generate_json(prompt=prompt)
            return response
        except Exception as e:
            logger.error(f"LLM price estimation failed: {e}")
            # Fallback to simple average
            avg = sum(comparable_prices) / len(comparable_prices) if comparable_prices else 0
            return {
                "price_low": avg * 0.8,
                "price_mid": avg,
                "price_high": avg * 1.2,
                "reasoning": f"Fallback estimate based on average: {e}",
            }
    
    def generate_justification(
        self,
        artwork_features: Dict[str, Any],
        price_range: Dict[str, float],
        comparables_analysis: Dict[str, Any],
        market_insights: Dict[str, Any],
        confidence_factors: Dict[str, Any],
        comparables: list,
    ) -> str:
        """Use LLM to generate comprehensive justification."""
        
        prompt = self._build_justification_prompt(
            artwork_features, price_range, comparables_analysis,
            market_insights, confidence_factors, comparables
        )
        
        try:
            response = self.client.generate_text(prompt=prompt)
            return response
        except Exception as e:
            logger.error(f"LLM justification failed: {e}")
            return f"Price estimate: ${price_range.get('mid', 0):,.2f}. Error generating detailed justification: {e}"
    
    def research_artist(
        self,
        author: str,
        year_created: str,
        artwork_type: str,
        title: str,
        market_insights: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Research artist background and market position."""
        
        prompt = self._build_artist_research_prompt(
            author=author,
            year_created=year_created,
            artwork_type=artwork_type,
            title=title,
            market_insights=market_insights,
        )
        
        try:
            response = self.client.generate_json(prompt=prompt)
            return response
        except Exception as e:
            logger.error(f"LLM artist research failed: {e}")
            return {
                "artist_background": f"Unable to research artist: {e}",
                "artist_market_level": "unknown",
                "estimated_price_impact": "Unable to determine",
                "research_notes": [f"Error: {e}"],
            }
    
    def _build_comparables_prompt(
        self,
        artwork_features: Dict[str, Any],
        comparables: list,
        artwork_type: str,
    ) -> str:
        """Build prompt for analyzing comparables."""
        
        vision_features = artwork_features.get("vision_features", {})
        
        comp_summary = []
        for i, comp in enumerate(comparables[:5], 1):
            comp_summary.append(
                f"{i}. \"{comp.get('title', 'Unknown')}\" by {comp.get('author', 'Unknown')} - "
                f"${comp.get('price', 0):,.2f} (similarity: {comp.get('similarity_score', 0):.1%})"
            )
        
        prompt = f"""You are an expert art appraiser analyzing an {artwork_type} for valuation.

TARGET ARTWORK FEATURES:
{json.dumps(vision_features, indent=2)}

TOP COMPARABLE ARTWORKS:
{chr(10).join(comp_summary)}

Analyze these comparables and provide:
1. key_similarities: List of key similarities to target artwork
2. key_differences: List of important differences
3. quality_assessment: Overall quality assessment of comparables as references
4. market_position: Where target artwork sits in this market segment

Return as JSON with these exact keys."""
        
        return prompt
    
    def _build_pricing_prompt(
        self,
        artwork_features: Dict[str, Any],
        comparables_analysis: Dict[str, Any],
        market_insights: Dict[str, Any],
        comparable_prices: list,
    ) -> str:
        """Build prompt for price estimation."""
        
        prompt = f"""You are an expert art appraiser estimating price for an artwork.

COMPARABLE PRICES:
{comparable_prices}

COMPARABLES ANALYSIS:
{json.dumps(comparables_analysis, indent=2)}

MARKET INSIGHTS:
- Average: ${market_insights.get('avg_price', 0):,.2f}
- Median: ${market_insights.get('median_price', 0):,.2f}
- Trend: {market_insights.get('trend_direction', 'unknown')}
- Recent sales: {market_insights.get('num_recent_sales', 0)}

Based on this data, estimate a price range (low, mid, high) in USD.

Consider:
- Similarity scores and quality of comparables
- Market position and trends  
- Quality differences noted in analysis
- Price variance in the market

Return JSON with:
- price_low: lower bound
- price_mid: most likely price
- price_high: upper bound
- reasoning: brief explanation of your estimate"""
        
        return prompt
    
    def _build_justification_prompt(
        self,
        artwork_features: Dict[str, Any],
        price_range: Dict[str, float],
        comparables_analysis: Dict[str, Any],
        market_insights: Dict[str, Any],
        confidence_factors: Dict[str, Any],
        comparables: list,
    ) -> str:
        """Build prompt for generating justification."""
        
        top_comps = sorted(comparables, key=lambda x: x.get('similarity_score', 0), reverse=True)[:3]
        
        prompt = f"""You are an expert art appraiser preparing a professional valuation report.

PRICE ESTIMATE:
Low: ${price_range.get('low', 0):,.2f}
Mid: ${price_range.get('mid', 0):,.2f} (most likely)
High: ${price_range.get('high', 0):,.2f}

CONFIDENCE: {confidence_factors.get('avg_similarity', 0):.1%} based on {confidence_factors.get('num_comparables', 0)} comparables

COMPARABLES ANALYSIS:
{json.dumps(comparables_analysis, indent=2)}

TOP COMPARABLES:
{json.dumps([{
    'title': c.get('title'),
    'author': c.get('author'),
    'price': c.get('price'),
    'similarity': c.get('similarity_score'),
} for c in top_comps], indent=2)}

MARKET INSIGHTS:
{json.dumps(market_insights, indent=2)}

Write a comprehensive, professional valuation justification that includes:
1. Clear price estimate with range
2. Confidence level assessment
3. Methodology explanation
4. Analysis of comparable artworks
5. Market context and trends
6. Key factors affecting the valuation
7. Any important caveats or limitations

Be authoritative but honest about uncertainties. Use professional auction house language."""
        
        return prompt
    
    def _build_artist_research_prompt(
        self,
        author: str,
        year_created: str,
        artwork_type: str,
        title: str,
        market_insights: Dict[str, Any],
    ) -> str:
        """Build prompt for researching artist background and market position."""
        
        prompt = f"""You are an art market researcher analyzing artist information and estimating market positioning.

ARTIST INFORMATION:
- Name: {author}
- Year Created: {year_created}
- Artwork Type: {artwork_type}
- Artwork Title: {title}

MARKET CONTEXT:
- Market Average: ${market_insights.get('avg_price', 0):,.2f}
- Market Median: ${market_insights.get('median_price', 0):,.2f}
- Market Trend: {market_insights.get('trend_direction', 'unknown')}

Based on the artist name and year, provide research on:
1. artist_background: Brief background about the artist (nationality, style, historical significance)
2. artist_market_level: Classification like "Emerging", "Established", "Master", "Blue-chip" etc.
3. estimated_price_impact: How this artist's market position affects valuation (+20% premium, -10% discount, etc.)
4. research_notes: Any relevant findings or caveats

Return as JSON with these exact keys. If artist is unknown or cannot be researched, indicate that clearly."""
        
        return prompt
