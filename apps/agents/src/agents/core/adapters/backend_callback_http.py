from __future__ import annotations

import logging
from typing import Any

from agents.core.constants import (
    DEFAULT_HTTP_TIMEOUT_SECONDS,
    ITEM_FEATURES_CALLBACK_PATH_TEMPLATE,
    VISUALIZATION_CALLBACK_PATH_TEMPLATE,
)
from agents.core.ports import BackendCallbackClient
from agents.core.settings import get_settings
from agents.core.types import JobStatus
from agents.core.utils.errors import redacted_exc_info
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
        url = f"{settings.backend_url}{VISUALIZATION_CALLBACK_PATH_TEMPLATE.format(job_id=job_id)}"
        payload = {
            "status": status.value,
            "result_description": result_description,
            "error_message": error_message,
        }

        headers = internal_auth_headers(settings.INTERNAL_TOKEN)

        try:
            response = put_json(
                url,
                payload,
                headers=headers,
                timeout=DEFAULT_HTTP_TIMEOUT_SECONDS,
            )
            if response.status_code >= 400:
                logger.warning(
                    "failed to update visualizer job",
                    extra={
                        "task_name": "backend_callback.update_visualization",
                        "job_id": job_id,
                        "status": response.status_code,
                        "url": loggable_url(url),
                    },
                )
        except Exception as exc:
            logger.exception(
                "failed to send visualizer job update",
                extra={
                    "task_name": "backend_callback.update_visualization",
                    "job_id": job_id,
                    "url": loggable_url(url),
                    "error_type": type(exc).__name__,
                },
                exc_info=redacted_exc_info(exc, include_traceback=False),
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

        url = (
            f"{settings.backend_url}{ITEM_FEATURES_CALLBACK_PATH_TEMPLATE.format(item_id=item_id)}"
        )
        payload = {"features": sanitized_features}

        headers = internal_auth_headers(settings.INTERNAL_TOKEN)

        try:
            response = put_json(
                url,
                payload,
                headers=headers,
                timeout=DEFAULT_HTTP_TIMEOUT_SECONDS,
            )
            if response.status_code >= 400:
                logger.warning(
                    "failed to update feature extraction job",
                    extra={
                        "task_name": "backend_callback.update_item_features",
                        "item_id": item_id,
                        "status": response.status_code,
                        "url": loggable_url(url),
                    },
                )
        except Exception as exc:
            logger.exception(
                "failed to send feature extraction job update",
                extra={
                    "task_name": "backend_callback.update_item_features",
                    "item_id": item_id,
                    "url": loggable_url(url),
                    "error_type": type(exc).__name__,
                },
                exc_info=redacted_exc_info(exc, include_traceback=False),
            )
