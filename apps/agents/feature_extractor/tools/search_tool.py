from __future__ import annotations

import logging
from typing import Dict, List
from urllib.parse import urlsplit, urlunsplit

import httpx

from core.settings import get_settings

logger = logging.getLogger(__name__)


def _loggable_url(url: str) -> str:
    parsed = urlsplit(url)
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, "", ""))


def serpapi_search(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """
    Minimal SerpAPI-based Google results.
    Env var: SERPAPI_API_KEY
    Returns: [{title, snippet, url}]
    """
    api_key = get_settings().SERPAPI_API_KEY
    if not api_key:
        raise RuntimeError("SERPAPI_API_KEY not set. Configure a search provider.")

    params = {
        "engine": "google",
        "q": query,
        "api_key": api_key,
        "num": max_results,
    }

    try:
        with httpx.Client(timeout=20.0) as client:
            r = client.get("https://serpapi.com/search.json", params=params)
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
                "url": _loggable_url(str(e.request.url)),
                "error_type": type(e).__name__,
            },
        )
        raise
    except httpx.HTTPError as e:
        logger.error(
            "SerpAPI request failed",
            extra={
                "url": _loggable_url("https://serpapi.com/search.json"),
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
