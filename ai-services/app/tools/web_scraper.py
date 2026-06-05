"""Web scraper tool.

Extracts clean text content from a URL using httpx + BeautifulSoup4.
Results are cached in Firestore collection "webCache" with a 24h TTL.
"""

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone

import httpx

try:
    from bs4 import BeautifulSoup  # type: ignore
    _BS4_AVAILABLE = True
except Exception:  # pragma: no cover - optional dependency
    BeautifulSoup = None  # type: ignore
    _BS4_AVAILABLE = False

from app.core.firebase import get_firestore_client
from app.core.logging import get_logger

_logger = get_logger("web-scraper")
_TIMEOUT = 10.0
_MAX_CHARS = 12_000   # ≈ 3000 tokens
_CACHE_TTL = 86_400   # 24 hours

_NOISE_TAGS = ["nav", "footer", "header", "script", "style", "aside",
               "advertisement", "ads", "cookie", "banner"]


@dataclass
class ScrapedContent:
    title: str
    content: str
    url: str
    scraped_at: str


def _url_key(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()[:32]


def _get_cache(url: str) -> ScrapedContent | None:
    client = get_firestore_client()
    if client is None:
        return None
    try:
        key = _url_key(url)
        doc = client.collection("webCache").document(key).get()
        if not doc.exists:
            return None
        data = doc.to_dict()
        if datetime.now(timezone.utc).timestamp() > data.get("expiresAt", 0):
            client.collection("webCache").document(key).delete()
            return None
        return ScrapedContent(
            title=data.get("title", ""),
            content=data.get("content", ""),
            url=url,
            scraped_at=data.get("scrapedAt", ""),
        )
    except Exception as exc:
        _logger.warning("web_cache_get_failed url=%s reason=%s", url[:60], exc)
        return None


def _set_cache(url: str, result: ScrapedContent) -> None:
    client = get_firestore_client()
    if client is None:
        return
    try:
        key = _url_key(url)
        expires_at = datetime.now(timezone.utc).timestamp() + _CACHE_TTL
        client.collection("webCache").document(key).set({
            "url": url,
            "title": result.title,
            "content": result.content,
            "scrapedAt": result.scraped_at,
            "expiresAt": expires_at,
        })
    except Exception as exc:
        _logger.warning("web_cache_set_failed url=%s reason=%s", url[:60], exc)


def scrape(url: str) -> ScrapedContent | None:
    """Fetch and extract clean text from a URL. Returns None on failure."""
    if not _BS4_AVAILABLE:
        _logger.warning(
            "web_scraper disabled: beautifulsoup4 not installed. "
            "Run `pip install beautifulsoup4` to enable web scraping."
        )
        return None

    cached = _get_cache(url)
    if cached:
        return cached

    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (compatible; KNBBot/1.0; +https://knbdev.cm/bot)"
            )
        }
        with httpx.Client(timeout=_TIMEOUT, follow_redirects=True, verify=False) as client:
            resp = client.get(url, headers=headers)
            resp.raise_for_status()
            html = resp.text
    except httpx.TimeoutException:
        _logger.warning("web_scraper timeout url=%s", url[:60])
        return None
    except Exception as exc:
        _logger.warning("web_scraper fetch_failed url=%s reason=%s", url[:60], exc)
        return None

    try:
        soup = BeautifulSoup(html, "html.parser")
        # Remove noise tags
        for tag in soup.find_all(_NOISE_TAGS):
            tag.decompose()

        title = ""
        if soup.title:
            title = soup.title.get_text(strip=True)[:200]
        h1 = soup.find("h1")
        if h1:
            title = title or h1.get_text(strip=True)[:200]

        # Extract main content preferring semantic elements
        main = (
            soup.find("main")
            or soup.find("article")
            or soup.find(attrs={"role": "main"})
            or soup.body
        )
        if main is None:
            return None

        parts = []
        for tag in main.find_all(["h1", "h2", "h3", "p", "li"]):
            text = tag.get_text(separator=" ", strip=True)
            if len(text) > 20:
                parts.append(text)

        content = " ".join(parts)
        # Truncate to token budget
        if len(content) > _MAX_CHARS:
            content = content[:_MAX_CHARS].rsplit(" ", 1)[0] + "…"

        scraped_at = datetime.now(timezone.utc).isoformat()
        result = ScrapedContent(title=title, content=content, url=url, scraped_at=scraped_at)
        _set_cache(url, result)
        return result
    except Exception as exc:
        _logger.warning("web_scraper parse_failed url=%s reason=%s", url[:60], exc)
        return None
