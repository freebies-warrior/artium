from __future__ import annotations

import logging
from typing import Optional

from langgraph.graph import StateGraph, END
from langgraph.types import Command

from .types import FeatureState
from .llm_client import VisionLLMClient
from .brushstroke_node import brushstroke_node
from .blending_node import blending_node
from .physicality_node import physicality_node
from .vision_aggregate import vision_aggregate_node
from .material_node import material_node
from .form_node import form_node
from .surface_node import surface_node
from .craftsmanship_node import craftsmanship_node
from .vision_aggregate_sculpture import vision_aggregate_sculpture_node
from .market_agent import market_intelligence_node
from .tools.search_tool import serpapi_search

logger = logging.getLogger(__name__)


def state_coordinator_node(state: FeatureState) -> Command:
    """
    Hub node that routes based on artwork_type.
    For paintings: dispatch to brushstroke, blending, physicality
    For sculptures: dispatch to material, form, surface, craftsmanship
    Always eventually dispatch to market_agent and finalize.
    """
    have_vision = "vision_features" in state
    have_market = "market_features" in state
    artwork_type = state.get("artwork_type", "painting").lower()

    if have_vision and have_market:
        return Command(goto="finalize")

    targets = []

    if not have_vision:
        if artwork_type == "painting":
            have_brush = "vision_brushstroke" in state
            have_blend = "vision_blending" in state
            have_phys = "vision_physicality" in state
            
            if not have_brush:
                targets.append("brushstroke_agent")
            if not have_blend:
                targets.append("blending_agent")
            if not have_phys:
                targets.append("physicality_agent")
            if have_brush and have_blend and have_phys:
                targets.append("vision_aggregate_painting")
        
        elif artwork_type == "sculpture":
            have_material = "vision_material" in state
            have_form = "vision_form" in state
            have_surface = "vision_surface" in state
            have_craft = "vision_craftsmanship" in state
            
            if not have_material:
                targets.append("material_agent")
            if not have_form:
                targets.append("form_agent")
            if not have_surface:
                targets.append("surface_agent")
            if not have_craft:
                targets.append("craftsmanship_agent")
            if have_material and have_form and have_surface and have_craft:
                targets.append("vision_aggregate_sculpture")

    if not have_market:
        targets.append("market_agent")

    if len(targets) == 1:
        return Command(goto=targets[0])
    if len(targets) > 1:
        return Command(goto=targets)

    return Command(goto="finalize")


def finalize_node(state: FeatureState) -> Command:
    # You can compute derived “author_popularity_score” etc. here if you want.
    logger.info("Finalizing state.")
    return Command(goto=END)


def build_graph(vision_llm: VisionLLMClient):
    g = StateGraph(FeatureState)

    g.add_node("state_coordinator", state_coordinator_node)
    
    # Painting branch
    g.add_node("brushstroke_agent", brushstroke_node(vision_llm))
    g.add_node("blending_agent", blending_node(vision_llm))
    g.add_node("physicality_agent", physicality_node(vision_llm))
    g.add_node("vision_aggregate_painting", vision_aggregate_node())
    
    # Sculpture branch
    g.add_node("material_agent", material_node(vision_llm))
    g.add_node("form_agent", form_node(vision_llm))
    g.add_node("surface_agent", surface_node(vision_llm))
    g.add_node("craftsmanship_agent", craftsmanship_node(vision_llm))
    g.add_node("vision_aggregate_sculpture", vision_aggregate_sculpture_node())
    
    # Shared nodes
    g.add_node("market_agent", market_intelligence_node(search_fn=serpapi_search))
    g.add_node("finalize", finalize_node)

    g.set_entry_point("state_coordinator")

    # Painting branch edges (extraction nodes → aggregator → coordinator)
    g.add_edge("brushstroke_agent", "vision_aggregate_painting")
    g.add_edge("blending_agent", "vision_aggregate_painting")
    g.add_edge("physicality_agent", "vision_aggregate_painting")
    g.add_edge("vision_aggregate_painting", "state_coordinator")
    
    # Sculpture branch edges (extraction nodes → aggregator → coordinator)
    g.add_edge("material_agent", "vision_aggregate_sculpture")
    g.add_edge("form_agent", "vision_aggregate_sculpture")
    g.add_edge("surface_agent", "vision_aggregate_sculpture")
    g.add_edge("craftsmanship_agent", "vision_aggregate_sculpture")
    g.add_edge("vision_aggregate_sculpture", "state_coordinator")
    
    # Shared edges
    g.add_edge("market_agent", "state_coordinator")
    g.add_edge("state_coordinator", "finalize")
    g.add_edge("finalize", END)

    return g.compile()
