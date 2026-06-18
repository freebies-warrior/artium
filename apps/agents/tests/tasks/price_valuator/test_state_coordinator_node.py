from __future__ import annotations

from path_bootstrap import ensure_src_on_path

ensure_src_on_path()

import agents.tasks.price_valuator.nodes.state_coordinator_node as coordinator_module


def test_synthesize_report_contains_core_sections() -> None:
    report = coordinator_module._synthesize_report(
        price_range={"low": 1000, "mid": 1500, "high": 2000},
        comparables=[
            {"title": "Comp A", "author": "Artist A", "price": 1200, "similarity_score": 0.8},
            {"title": "Comp B", "author": "Artist B", "price": 1800, "similarity_score": 0.9},
        ],
        market_insights={"avg_price": 1400, "median_price": 1300, "trend_direction": "up"},
        metadata_research={"author": "Main Artist", "year_created": 1990},
        comparables_analysis={"key_similarities": ["Color palette", "Subject matter"]},
        reasoning_steps=["Gather comparables", "Adjust for market context"],
    )

    assert "COMPREHENSIVE PRICE VALUATION REPORT" in report
    assert "Estimated Range: $1,000.00 - $2,000.00" in report
    assert "Most Likely Price: $1,500.00" in report
    assert "COMPARABLE ARTWORKS ANALYSIS" in report
    assert "VALUATION METHODOLOGY" in report
    assert "CONCLUSION" in report


def test_state_coordinator_node_adds_error_when_synthesis_fails(monkeypatch) -> None:
    def raise_error(**_kwargs):
        raise RuntimeError("coordination exploded")

    monkeypatch.setattr(coordinator_module, "_synthesize_report", raise_error)
    node = coordinator_module.state_coordinator_node()

    result = node({"errors": ["existing error"]})

    assert result.goto == "END"
    assert "Error during coordination: coordination exploded" == result.update["coordinator_report"]
    assert result.update["errors"] == [
        "existing error",
        "Coordination error: coordination exploded",
    ]
