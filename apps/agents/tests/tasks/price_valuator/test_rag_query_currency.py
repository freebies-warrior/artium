from __future__ import annotations

from path_bootstrap import ensure_src_on_path

ensure_src_on_path()

from agents.tasks.price_valuator.tools.rag_query import RAGQueryTool, _extract_currency


def test_extract_currency_prefers_metadata_and_defaults_to_sgd() -> None:
    assert _extract_currency({"currency": "usd"}) == "USD"
    assert _extract_currency({"sale_currency": "sgd"}) == "SGD"
    assert _extract_currency({"currency_code": "jpy"}) == "JPY"
    assert _extract_currency({}) == "SGD"


def test_extract_price_returns_whole_dollar_amounts() -> None:
    assert RAGQueryTool._extract_price(None, {"price": "1234.4"}) == 1234
    assert RAGQueryTool._extract_price(None, {"sale_price": 1234.6}) == 1235
    assert RAGQueryTool._extract_price(None, {}) == 0
