"""Web search tool.

Uses Brave Search API when BRAVE_API_KEY is set, otherwise falls back to
DuckDuckGo Instant Answer API (no key required).

Rate limiting: max 10 requests/minute via an in-memory sliding window.
"""

import time
from collections import deque
from dataclasses import dataclass

import httpx

from app.core.logging import get_logger
from app.core.settings import settings

_logger = get_logger("web-search")
_TIMEOUT = 8.0
_MAX_RPM = 10


@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str
    published_date: str = ""


class _RateLimiter:
    def __init__(self, max_per_minute: int) -> None:
        self._max = max_per_minute
        self._ts: deque[float] = deque()

    def acquire(self) -> bool:
        now = time.monotonic()
        while self._ts and now - self._ts[0] > 60:
            self._ts.popleft()
        if len(self._ts) >= self._max:
            return False
        self._ts.append(now)
        return True


_limiter = _RateLimiter(_MAX_RPM)


def _search_brave(query: str, max_results: int) -> list[SearchResult]:
    url = "https://api.search.brave.com/res/v1/web/search"
    headers = {
        "X-Subscription-Token": settings.brave_api_key,
        "Accept": "application/json",
    }
    params = {"q": query, "count": max_results}
    with httpx.Client(timeout=_TIMEOUT) as client:
        resp = client.get(url, headers=headers, params=params)
        resp.raise_for_status()
    data = resp.json()
    results = []
    for item in data.get("web", {}).get("results", [])[:max_results]:
        results.append(SearchResult(
            title=item.get("title", ""),
            url=item.get("url", ""),
            snippet=item.get("description", ""),
            published_date=item.get("age", ""),
        ))
    return results


def _search_duckduckgo(query: str, max_results: int) -> list[SearchResult]:
    # Tentative avec ddgs (vrais résultats web)
    try:
        from ddgs import DDGS
        results = []
        for item in DDGS().text(query, max_results=max_results):
            results.append(SearchResult(
                title=item.get("title", ""),
                url=item.get("href", ""),
                snippet=item.get("body", "")[:300],
            ))
        if results:
            return results
    except Exception as exc:
        _logger.warning("ddgs failed query=%s reason=%s — repli Instant Answer", query[:60], exc)

    # Repli : DuckDuckGo Instant Answer API
    url = "https://api.duckduckgo.com/"
    params = {"q": query, "format": "json", "no_html": "1", "skip_disambig": "1"}
    with httpx.Client(timeout=_TIMEOUT) as client:
        resp = client.get(url, params=params)
        resp.raise_for_status()
    data = resp.json()
    results = []
    if data.get("AbstractText"):
        results.append(SearchResult(
            title=data.get("Heading", query),
            url=data.get("AbstractURL", ""),
            snippet=data.get("AbstractText", "")[:300],
        ))
    for topic in data.get("RelatedTopics", [])[:max_results]:
        if isinstance(topic, dict) and topic.get("Text"):
            results.append(SearchResult(
                title=topic.get("Text", "")[:80],
                url=topic.get("FirstURL", ""),
                snippet=topic.get("Text", "")[:300],
            ))
        if len(results) >= max_results:
            break
    return results


def search(query: str, max_results: int = 5) -> list[SearchResult]:
    """Search the web. Returns empty list on any failure."""
    if not _limiter.acquire():
        _logger.warning("web_search rate_limited query=%s", query[:60])
        return []
    try:
        if settings.brave_api_key:
            return _search_brave(query, max_results)
        return _search_duckduckgo(query, max_results)
    except httpx.TimeoutException:
        _logger.warning("web_search timeout query=%s", query[:60])
        return []
    except Exception as exc:
        _logger.warning("web_search failed query=%s reason=%s", query[:60], exc)
        return []
