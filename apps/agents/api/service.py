"""Unified service for managing feature extraction and visualization graphs."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any

from feature_extractor.graph import build_graph
from feature_extractor.types import FeatureState
from feature_extractor.llm_client import GeminiVisionClient
from visualizer.pipeline_langgraph import build_visualization_graph, VizState # maaf iya ni emang jelek soalnya mau cepet hehe
from visualizer.client import GeminiClient

logger = logging.getLogger(__name__)


class AgentService:
    """Unified service for managing both feature extraction and visualization graphs."""
    
    def __init__(self):
        self.feature_graph = None
        self.visualizer_graph = None
        self.feature_client = None
        self.visualizer_client = None
    
    def initialize(self):
        """Initialize both graphs and clients (called once at startup)."""
        logger.info("Initializing AgentService...")
        self.feature_client = GeminiVisionClient()
        self.feature_graph = build_graph(vision_llm=self.feature_client)
        self.visualizer_client = GeminiClient()
        self.visualizer_graph = build_visualization_graph()
        logger.info("AgentService initialized successfully.")
    
    def shutdown(self):
        """Clean up resources (called at shutdown)."""
        logger.info("Shutting down AgentService...")
        self.feature_graph = None
        self.visualizer_graph = None
        self.feature_client = None
        self.visualizer_client = None
        logger.info("AgentService shut down.")
    
    def extract_features(self, initial_state: FeatureState) -> FeatureState:
        """Extract features from artwork using the cached feature extraction graph."""
        if self.feature_graph is None:
            raise RuntimeError("AgentService not initialized. Call initialize() first.")
        
        logger.info("Extracting features...")
        result = self.feature_graph.invoke(initial_state)
        logger.info(f"Feature extraction complete. Artwork type: {result.get('artwork_type')}")
        return result
    
    def visualize(self, state: VizState) -> VizState:
        """Run visualization pipeline using the cached visualization graph."""
        if self.visualizer_graph is None:
            raise RuntimeError("AgentService not initialized. Call initialize() first.")
        
        logger.info("Running visualization pipeline...")
        result = self.visualizer_graph.invoke(state)
        logger.info("Visualization complete.")
        return result


# Global service instance
_agent_service: AgentService | None = None


def get_agent_service() -> AgentService:
    """Get the global agent service instance."""
    global _agent_service
    if _agent_service is None:
        raise RuntimeError("Agent service not initialized")
    return _agent_service


@asynccontextmanager
async def agent_service_lifespan():
    """Async context manager for agent service lifecycle."""
    global _agent_service
    
    # Startup
    _agent_service = AgentService()
    _agent_service.initialize()
    
    yield
    
    # Shutdown
    if _agent_service:
        _agent_service.shutdown()
        _agent_service = None
