from __future__ import annotations

from path_bootstrap import ensure_src_on_path

ensure_src_on_path()

from agents.tasks.price_valuator.llm_client import ValuationLLMClient


class _FailingVisionClient:
    def __init__(self, model: str) -> None:
        self.model = model

    def generate_json(self, prompt: str):  # noqa: ANN201
        raise RuntimeError("provider error with SECRET=abc123")

    def generate_text(self, prompt: str) -> str:
        raise RuntimeError("provider error with SECRET=abc123")


def test_estimate_price_range_fallback_reasoning_does_not_leak_exception(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "agents.tasks.price_valuator.llm_client.VisionLLMClient",
        _FailingVisionClient,
    )
    client = ValuationLLMClient()

    result = client.estimate_price_range(
        artwork_features={},
        comparables_analysis={},
        market_insights={},
        comparable_prices=[1000, 2000, 3000],
    )

    assert result["reasoning"] == "Fallback estimate based on average due to model error."
    assert "SECRET=abc123" not in result["reasoning"]


def test_generate_justification_fallback_does_not_leak_exception(monkeypatch) -> None:
    monkeypatch.setattr(
        "agents.tasks.price_valuator.llm_client.VisionLLMClient",
        _FailingVisionClient,
    )
    client = ValuationLLMClient()

    text = client.generate_justification(
        artwork_features={},
        price_range={"mid": 1234.56},
        comparables_analysis={},
        market_insights={},
        confidence_factors={},
        comparables=[],
    )

    assert "SECRET=abc123" not in text
    assert "Detailed justification unavailable due to model error." in text


def test_research_artist_fallback_does_not_leak_exception(monkeypatch) -> None:
    monkeypatch.setattr(
        "agents.tasks.price_valuator.llm_client.VisionLLMClient",
        _FailingVisionClient,
    )
    client = ValuationLLMClient()

    result = client.research_artist(
        author="Author",
        year_created="2020",
        artwork_type="painting",
        title="Title",
        market_insights={},
    )

    assert result["artist_background"] == "Unable to research artist at this time."
    assert result["research_notes"] == ["Artist research unavailable due to model error."]
