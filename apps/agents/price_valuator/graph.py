"""Price valuation graph builder."""

from __future__ import annotations

import logging
from langgraph.graph import StateGraph, END

from .types import ValuationState
from .tools.rag_query import RAGQueryTool
from .nodes.rag_search_node import rag_search_node
from .nodes.market_analysis_node import market_analysis_node
from .nodes.metadata_research_node import metadata_research_node
from .nodes.price_calculation_node import price_calculation_node
from .nodes.state_coordinator_node import state_coordinator_node

logger = logging.getLogger(__name__)


def build_valuation_graph(config_path: str = None):
    """
    Build the price valuation graph.

    The graph follows this flow:
    1. RAG search: Find comparable artworks in Pinecone
    2. Market analysis: Analyze comparable sales data with LLM insights
    3. Metadata research: Research artist background and historical context
    4. Price calculation: Estimate price range with LLM reasoning
    5. State coordinator: Gather all reports and generate final comprehensive report

    Args:
        config_path: Path to config.yaml for RAG configuration

    Returns:
        Compiled LangGraph graph
    """
    logger.info("Building price valuation graph...")

    # Initialize RAG tool
    rag_tool = RAGQueryTool(config_path=config_path)

    # Create graph
    graph = StateGraph(ValuationState)

    # Add nodes
    graph.add_node("rag_search", rag_search_node(rag_tool))
    graph.add_node("market_analysis", market_analysis_node())
    graph.add_node("metadata_research", metadata_research_node())
    graph.add_node("price_calculation", price_calculation_node())
    graph.add_node("state_coordinator", state_coordinator_node())

    # Set entry point
    graph.set_entry_point("rag_search")

    # Nodes handle their own routing via Command.goto
    # No need to add explicit edges since Command handles transitions

    # Compile graph
    compiled_graph = graph.compile()

    logger.info("Price valuation graph built successfully")
    return compiled_graph
