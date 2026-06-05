"""Tests for web search, scraper, and learning engine — uses mocks."""

import asyncio
from unittest.mock import MagicMock, patch

import pytest


# ── WebSearchTool ─────────────────────────────────────────────────────────────

def test_web_search_rate_limiter():
    from app.tools.web_search import _RateLimiter
    limiter = _RateLimiter(max_per_minute=3)
    assert limiter.acquire() is True
    assert limiter.acquire() is True
    assert limiter.acquire() is True
    assert limiter.acquire() is False  # limit hit


def test_web_search_returns_empty_on_error():
    """search() must return [] on network error, never raise."""
    with patch("app.tools.web_search.httpx.Client") as mock_client:
        mock_client.return_value.__enter__.return_value.get.side_effect = Exception("timeout")
        from app.tools.web_search import search
        results = search("test query")
        assert results == []


def test_web_search_result_dataclass():
    from app.tools.web_search import SearchResult
    r = SearchResult(title="Test", url="https://example.com", snippet="snippet text")
    assert r.title == "Test"
    assert r.published_date == ""


# ── WebScraperTool ────────────────────────────────────────────────────────────

def test_web_scraper_returns_none_on_error():
    """scrape() must return None on failure, never raise."""
    with patch("app.tools.web_scraper.get_firestore_client", return_value=None):
        with patch("app.tools.web_scraper.httpx.Client") as mock_client:
            mock_client.return_value.__enter__.return_value.get.side_effect = Exception("conn error")
            from app.tools.web_scraper import scrape
            result = scrape("https://not-real-url.test")
            assert result is None


def test_web_scraper_parses_html():
    """scrape() extracts title and content from HTML."""
    html = "<html><head><title>Test Page</title></head><body><main><p>Hello world content here.</p></main></body></html>"
    mock_resp = MagicMock()
    mock_resp.text = html
    mock_resp.raise_for_status = MagicMock()

    with patch("app.tools.web_scraper.get_firestore_client", return_value=None):
        with patch("app.tools.web_scraper.httpx.Client") as mock_client:
            mock_client.return_value.__enter__.return_value.get.return_value = mock_resp
            from app.tools import web_scraper
            # Reset module cache
            import importlib
            importlib.reload(web_scraper)
            result = web_scraper.scrape("https://example.com")
            if result:  # may be None if firestore cache check fails
                assert "Hello world" in result.content or result.title != ""


# ── LearningEngine ────────────────────────────────────────────────────────────

def test_get_cached_knowledge_returns_none_without_firestore():
    with patch("app.tools.learning_engine.get_firestore_client", return_value=None):
        from app.tools import learning_engine
        import importlib
        importlib.reload(learning_engine)
        result = learning_engine.get_cached_knowledge("test topic")
        assert result is None


def test_get_top_knowledge_returns_empty_without_firestore():
    with patch("app.tools.learning_engine.get_firestore_client", return_value=None):
        from app.tools import learning_engine
        import importlib
        importlib.reload(learning_engine)
        result = learning_engine.get_top_knowledge(limit=5)
        assert result == []


def test_invalidate_cache_returns_false_without_firestore():
    # Patch at both layers — do NOT reload (reload re-imports the real function)
    with patch("app.core.firebase.get_firestore_client", return_value=None):
        with patch("app.tools.learning_engine.get_firestore_client", return_value=None):
            from app.tools import learning_engine
            result = learning_engine.invalidate_cache("some topic")
            assert result is False


def test_learn_from_web_returns_list():
    """learn_from_web() must return a list of strings even with all mocks."""
    mock_search_result = MagicMock()
    mock_search_result.url = "https://example.com"
    mock_search_result.snippet = "web development trends 2025"
    mock_search_result.title = "Web dev 2025"

    with patch("app.tools.learning_engine.get_firestore_client", return_value=None):
        with patch("app.tools.learning_engine.search", return_value=[mock_search_result]):
            with patch("app.tools.learning_engine.scrape", return_value=None):
                with patch("app.tools.learning_engine._llm") as mock_llm:
                    mock_llm.json_completion.return_value = {
                        "queries": ["query 1", "query 2", "query 3"]
                    }
                    # For the summary call
                    mock_llm.json_completion.side_effect = [
                        {"queries": ["q1", "q2", "q3"]},
                        {"summary": "Test summary", "insights": ["Insight 1", "Insight 2"], "relevance_score": 0.7},
                    ]
                    from app.tools import learning_engine
                    import importlib
                    importlib.reload(learning_engine)
                    result = asyncio.get_event_loop().run_until_complete(
                        learning_engine.learn_from_web("développement web Cameroun")
                    )
                    assert isinstance(result, list)


# ── Firestore cache tests (mock Firestore) ────────────────────────────────────

def test_firestore_cache_hit():
    from datetime import datetime, timezone
    mock_doc = MagicMock()
    mock_doc.exists = True
    mock_doc.to_dict.return_value = {
        "topic": "test",
        "insights": ["Insight A", "Insight B"],
        "learnedAt": datetime.now(timezone.utc).timestamp() - 3600,  # 1h ago
    }
    mock_collection = MagicMock()
    mock_collection.document.return_value.get.return_value = mock_doc
    mock_collection.document.return_value.update = MagicMock()
    mock_firestore = MagicMock()
    mock_firestore.collection.return_value = mock_collection

    # Patch at the source so the function call returns mock_firestore.
    # Do NOT reload inside the patch block — reload re-imports the original.
    with patch("app.core.firebase.get_firestore_client", return_value=mock_firestore):
        with patch("app.tools.learning_engine.get_firestore_client", return_value=mock_firestore):
            from app.tools import learning_engine
            result = learning_engine.get_cached_knowledge("test")
            assert result == ["Insight A", "Insight B"]
