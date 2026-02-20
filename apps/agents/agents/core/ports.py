from __future__ import annotations

from typing import Any, Protocol


class BackendCallbackClient(Protocol):
    """Port for reporting asynchronous job results back to backend service."""

    def update_visualization(
        self,
        job_id: str,
        status: str,
        result_description: str | None,
        error_message: str | None,
    ) -> None: ...

    def update_item_features(
        self,
        item_id: Any,
        feature_json: dict[str, Any],
    ) -> None: ...
