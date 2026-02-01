from __future__ import annotations

import logging
import os
from typing import Dict, List

import httpx
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()


def serpapi_search(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """
    Minimal SerpAPI-based Google results.
    Env var: SERPAPI_API_KEY
    Returns: [{title, snippet, url}]
    """
    api_key = os.getenv("SERPAPI_API_KEY")
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
