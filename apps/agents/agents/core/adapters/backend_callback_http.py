from __future__ import annotations

import logging
from typing import Any

from agents.core.ports import BackendCallbackClient
from agents.core.settings import get_settings
from agents.core.types import JobStatus
from agents.core.utils.http import internal_auth_headers, loggable_url, put_json
from agents.core.utils.json import sanitize_for_json

logger = logging.getLogger(__name__)


class HttpBackendCallbackClient(BackendCallbackClient):
    """HTTP adapter for sending async job updates to backend service."""

    def update_visualization(
        self,
        job_id: str,
        status: JobStatus,
        result_description: str | None,
        error_message: str | None,
    ) -> None:
        settings = get_settings()
        url = f"{settings.backend_url}/visualizations/{job_id}"
        payload = {
            "status": status.value,
            "result_description": result_description,
            "error_message": error_message,
        }

        headers = internal_auth_headers(settings.INTERNAL_TOKEN)

        try:
            response = put_json(url, payload, headers=headers, timeout=10.0)
            if response.status_code >= 400:
                logger.warning(
                    "failed to update visualizer job",
                    extra={
                        "job_id": job_id,
                        "status": response.status_code,
                        "url": loggable_url(url),
                    },
                )
        except Exception as exc:
            logger.error(
                "failed to send visualizer job update",
                extra={
                    "job_id": job_id,
                    "url": loggable_url(url),
                    "error_type": type(exc).__name__,
                },
            )

    def update_item_features(
        self,
        item_id: Any,
        feature_json: dict[str, Any],
    ) -> None:
        settings = get_settings()
        sanitized_features = sanitize_for_json(feature_json)
        if not isinstance(sanitized_features, dict):
            sanitized_features = {}

        url = f"{settings.backend_url}/items/{item_id}/features"
        payload = {"features": sanitized_features}

        headers = internal_auth_headers(settings.INTERNAL_TOKEN)

        try:
            response = put_json(url, payload, headers=headers, timeout=10.0)
            if response.status_code >= 400:
                logger.warning(
                    "failed to update feature extraction job",
                    extra={
                        "item_id": item_id,
                        "status": response.status_code,
                        "url": loggable_url(url),
                    },
                )
        except Exception as exc:
            logger.error(
                "failed to send feature extraction job update",
                extra={
                    "item_id": item_id,
                    "url": loggable_url(url),
                    "error_type": type(exc).__name__,
                },
            )
