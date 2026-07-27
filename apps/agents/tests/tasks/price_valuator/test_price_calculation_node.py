from __future__ import annotations

from path_bootstrap import ensure_src_on_path

ensure_src_on_path()

import agents.tasks.price_valuator.nodes.price_calculation_node as price_calculation_module


class _SuccessfulLLMClient:
    def __init__(self, *args, **kwargs) -> None:
        pass

    def estimate_price_range(self, **kwargs):  # noqa: ANN003, ANN201
        return {
            "price_low": 1234.2,
            "price_mid": 1567.8,
            "price_high": 1999.1,
            "reasoning": "LLM estimate",
        }


class _FailingLLMClient:
    def __init__(self, *args, **kwargs) -> None:
        pass

    def estimate_price_range(self, **kwargs):  # noqa: ANN003, ANN201
        raise RuntimeError("model unavailable")


def _state() -> dict:
    return {
        "comparables": [
            {"price": 1000, "currency": "SGD", "similarity_score": 1.0},
            {"price": 1000, "currency": "SGD", "similarity_score": 1.0},
        ],
        "market_insights": {"median_price": 1000, "price_std": 0},
        "artwork_features": {},
        "comparables_analysis": {},
    }


def test_price_calculation_node_quantizes_llm_estimates_to_sgd_dollars(monkeypatch) -> None:
    monkeypatch.setattr(
        price_calculation_module,
        "ValuationLLMClient",
        _SuccessfulLLMClient,
    )

    node = price_calculation_module.price_calculation_node()
    result = node(_state())

    assert result.goto == "state_coordinator"
    assert result.update["price_range"] == {"low": 1234, "mid": 1568, "high": 1999}
    assert result.update["currency"] == "SGD"


def test_price_calculation_node_fallback_keeps_sgd_currency_and_whole_dollars(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        price_calculation_module,
        "ValuationLLMClient",
        _FailingLLMClient,
    )

    node = price_calculation_module.price_calculation_node()
    result = node(_state())

    assert result.goto == "state_coordinator"
    assert result.update["price_range"] == {"low": 850, "mid": 1000, "high": 1150}
    assert result.update["currency"] == "SGD"
