from __future__ import annotations

from path_bootstrap import ensure_src_on_path

ensure_src_on_path()

from agents.providers.rag.ingest.ingest_csv import (
    _append_vector_batch,
    _flush_remaining_batches,
)


class _RecordingIndex:
    def __init__(self) -> None:
        self.calls: list[tuple[list[tuple[str, list[float], dict[str, object]]], str]] = []

    def upsert(self, *, vectors, namespace):  # noqa: ANN001, ANN201
        self.calls.append((list(vectors), namespace))


def test_mixed_batches_flush_to_matching_indexes() -> None:
    indexes = {"painting": _RecordingIndex(), "sculpture": _RecordingIndex()}
    batches = {"painting": [], "sculpture": []}

    _append_vector_batch(
        idx=indexes,
        batches=batches,
        artwork_type="painting",
        vector_item=("p1", [1.0], {"kind": "painting"}),
        namespace="ns",
        upsert_batch_size=2,
    )
    _append_vector_batch(
        idx=indexes,
        batches=batches,
        artwork_type="sculpture",
        vector_item=("s1", [2.0], {"kind": "sculpture"}),
        namespace="ns",
        upsert_batch_size=2,
    )
    _append_vector_batch(
        idx=indexes,
        batches=batches,
        artwork_type="painting",
        vector_item=("p2", [3.0], {"kind": "painting"}),
        namespace="ns",
        upsert_batch_size=2,
    )

    _flush_remaining_batches(idx=indexes, batches=batches, namespace="ns")

    assert indexes["painting"].calls == [
        ([("p1", [1.0], {"kind": "painting"}), ("p2", [3.0], {"kind": "painting"})], "ns")
    ]
    assert indexes["sculpture"].calls == [([("s1", [2.0], {"kind": "sculpture"})], "ns")]
