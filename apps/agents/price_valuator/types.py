"""Types for price valuation agent."""

from __future__ import annotations

import operator
from typing import Annotated, Any, Dict, List, TypedDict

from pydantic import BaseModel, Field


class PriceRange(BaseModel):
    """Price estimate range."""

    low: float = Field(description="Lower bound of price estimate")
    mid: float = Field(description="Mid-point estimate (most likely price)")
    high: float = Field(description="Upper bound of price estimate")
    currency: str = Field(default="USD", description="Currency code")


class ComparableArtwork(BaseModel):
    """Comparable artwork from RAG search."""

    id: str = Field(description="Vector ID from Pinecone")
    similarity_score: float = Field(description="Similarity to query artwork (0-1)")
    price: float = Field(description="Sale price")
    title: str = Field(default="Unknown")
    author: str = Field(default="Unknown")
    sale_date: str = Field(default="")
    location: str = Field(default="")
    features_preview: str = Field(default="", description="Preview of artwork features")


class ConfidenceFactors(BaseModel):
    """Factors affecting confidence score."""

    num_comparables: int = Field(description="Number of similar artworks found")
    avg_similarity: float = Field(description="Average similarity score of comparables")
    price_variance: float = Field(description="Coefficient of variation in comparable prices")
    recency_score: float = Field(description="How recent the comparable sales are (0-1)")
    feature_quality: float = Field(description="Quality of feature match (0-1)")


class MarketInsights(BaseModel):
    """Market analysis insights."""

    avg_price: float = Field(description="Average price of comparables")
    median_price: float = Field(description="Median price of comparables")
    price_std: float = Field(description="Standard deviation of prices")
    num_recent_sales: int = Field(description="Number of sales in last 12 months")
    trend_direction: str = Field(description="Price trend: rising, stable, declining")


class ValuationState(TypedDict, total=False):
    """State for price valuation graph."""

    # Input (from feature extractor)
    artwork_features: Dict[str, Any]
    metadata: Dict[str, Any]
    artwork_type: str  # "painting" or "sculpture"
    image_bytes: bytes

    # RAG search results
    comparables: List[Dict[str, Any]]  # Raw comparable data
    rag_search_summary: str

    # LLM-powered comparative analysis
    comparables_analysis: Dict[str, Any]

    # Artist/Historical research
    metadata_research: Dict[str, Any]

    # Market analysis
    market_insights: Dict[str, Any]
    price_trends: Dict[str, Any]

    # Price estimation
    price_range: Dict[str, float]  # {low, mid, high}
    currency: str

    # Final coordination and report
    coordinator_report: str
    final_justification: str

    # Justification
    justification: str  # Detailed explanation of the valuation
    reasoning_steps: List[str]  # Step-by-step reasoning

    # Control
    errors: Annotated[List[str], operator.add]


class ValuationResult(BaseModel):
    """Final valuation result."""

    price_range: PriceRange
    confidence_score: float = Field(ge=0.0, le=1.0)
    justification: str
    reasoning_steps: List[str]
    comparables: List[ComparableArtwork]
    market_insights: MarketInsights
    confidence_factors: ConfidenceFactors
    errors: List[str] = Field(default_factory=list)
