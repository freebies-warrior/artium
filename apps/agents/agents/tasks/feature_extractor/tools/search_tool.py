from __future__ import annotations

import logging
from typing import Dict, List

import httpx

from agents.core.constants import DEFAULT_SEARCH_TIMEOUT_SECONDS, SERPAPI_SEARCH_URL
from agents.core.settings import get_settings
from agents.core.utils.http import loggable_url

logger = logging.getLogger(__name__)


def serpapi_search(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """
    Minimal SerpAPI-based Google results.
    Env var: SERPAPI_API_KEY
    Returns: [{title, snippet, url}]
    """
    try:
        api_key = get_settings().require_serpapi_api_key()
    except ValueError as exc:
        raise RuntimeError(str(exc)) from exc

    params = {
        "engine": "google",
        "q": query,
        "api_key": api_key,
        "num": max_results,
    }

    try:
        with httpx.Client(timeout=DEFAULT_SEARCH_TIMEOUT_SECONDS) as client:
            r = client.get(SERPAPI_SEARCH_URL, params=params)
            r.raise_for_status()
            data = r.json()
    except httpx.HTTPStatusError as e:
        if e.response.status_code in (401, 403):
            logger.warning(
                "SerpAPI authentication failed (401/403). Invalid or expired API key. Market intelligence skipped."
            )
            return []
        logger.error(
            "SerpAPI request failed",
            extra={
                "status_code": e.response.status_code,
                "url": loggable_url(str(e.request.url)),
                "error_type": type(e).__name__,
            },
        )
        raise
    except httpx.HTTPError as e:
        logger.error(
            "SerpAPI request failed",
            extra={
                "url": loggable_url(SERPAPI_SEARCH_URL),
                "error_type": type(e).__name__,
            },
        )
        raise

    results: List[Dict[str, str]] = []
    for item in data.get("organic_results", [])[:max_results]:
        results.append(
            {
                "title": item.get("title", ""),
                "snippet": item.get("snippet", ""),
                "url": item.get("link", ""),
            }
        )

    logger.info("SerpAPI search query=%r -> %d results", query, len(results))
    return results
