from __future__ import annotations

from path_bootstrap import ensure_src_on_path

ensure_src_on_path()

from agents.tasks.price_valuator.nodes.rag_search_node import rag_search_node


class _FakeRAGTool:
    def search_comparables(self, feature_state, artwork_type, top_k=10):  # noqa: ANN001, ANN202
        return [
            {
                "price": 1000,
                "currency": "USD",
                "similarity_score": 0.9,
                "title": "Foreign comp",
            },
            {
                "price": 1200,
                "currency": "SGD",
                "similarity_score": 0.8,
                "title": "Local comp",
            },
        ]


def test_rag_search_node_filters_non_sgd_comparables() -> None:
    node = rag_search_node(_FakeRAGTool())

    result = node(
        {
            "artwork_type": "painting",
            "metadata": {},
            "artwork_features": {"vision_features": {}},
        }
    )

    assert result.goto == "market_analysis"
    assert result.update["comparables"] == [
        {
            "price": 1200,
            "currency": "SGD",
            "similarity_score": 0.8,
            "title": "Local comp",
        }
    ]
