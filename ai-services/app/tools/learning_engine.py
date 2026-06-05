"""Autonomous web learning engine.

Learns from the web about a topic, summarises with Claude, and caches
insights in Firestore collection "learnedKnowledge".
"""

import asyncio
from datetime import datetime, timezone

from app.core.firebase import get_firestore_client
from app.core.llm import LlmClient
from app.core.logging import get_logger
from app.tools.web_scraper import scrape
from app.tools.web_search import search

_logger = get_logger("learning-engine")
_COLLECTION = "learnedKnowledge"
_llm = LlmClient()


# ── cache helpers ─────────────────────────────────────────────────────────────

def _topic_key(topic: str) -> str:
    return topic.lower().strip()[:80].replace(" ", "_")


def get_cached_knowledge(topic: str, max_age_hours: int = 48) -> list[str] | None:
    """Return cached insights or None on cache miss."""
    client = get_firestore_client()
    if client is None:
        return None
    key = _topic_key(topic)
    try:
        doc = client.collection(_COLLECTION).document(key).get()
        if not doc.exists:
            return None
        data = doc.to_dict()
        learned_at = data.get("learnedAt", 0)
        age_hours = (datetime.now(timezone.utc).timestamp() - learned_at) / 3600
        if age_hours > max_age_hours:
            return None
        # Increment usage counter
        try:
            client.collection(_COLLECTION).document(key).update(
                {"usageCount": data.get("usageCount", 0) + 1}
            )
        except Exception:
            pass
        return data.get("insights", [])
    except Exception as exc:
        _logger.warning("get_cached_knowledge failed topic=%s reason=%s", topic[:40], exc)
        return None


def _save_knowledge(topic: str, summary: str, insights: list[str], sources: list[str],
                    context_hint: str, score: float) -> None:
    client = get_firestore_client()
    if client is None:
        return
    key = _topic_key(topic)
    try:
        client.collection(_COLLECTION).document(key).set({
            "topic": topic,
            "summary": summary,
            "insights": insights,
            "sources": sources,
            "relevanceScore": score,
            "contextHint": context_hint,
            "learnedAt": datetime.now(timezone.utc).timestamp(),
            "usageCount": 0,
        })
    except Exception as exc:
        _logger.warning("save_knowledge failed topic=%s reason=%s", topic[:40], exc)


def get_top_knowledge(limit: int = 10) -> list[dict]:
    """Return the N most-used knowledge entries."""
    client = get_firestore_client()
    if client is None:
        return []
    try:
        docs = list(
            client.collection(_COLLECTION)
            .order_by("usageCount", direction="DESCENDING")
            .limit(limit)
            .stream()
        )
        return [d.to_dict() for d in docs]
    except Exception as exc:
        _logger.warning("get_top_knowledge failed reason=%s", exc)
        return []


def invalidate_cache(topic: str) -> bool:
    """Delete cached knowledge for a topic. Returns True if deleted."""
    client = get_firestore_client()
    if client is None:
        return False
    key = _topic_key(topic)
    try:
        client.collection(_COLLECTION).document(key).delete()
        return True
    except Exception as exc:
        _logger.warning("invalidate_cache failed topic=%s reason=%s", topic[:40], exc)
        return False


def search_knowledge(topic: str) -> list[dict]:
    """Simple keyword search in learnedKnowledge (Firestore doesn't support full-text)."""
    client = get_firestore_client()
    if client is None:
        return []
    try:
        docs = list(client.collection(_COLLECTION).limit(100).stream())
        query_lower = topic.lower()
        results = []
        for doc in docs:
            data = doc.to_dict()
            t = data.get("topic", "").lower()
            if query_lower in t or t in query_lower:
                results.append(data)
        return results[:10]
    except Exception as exc:
        _logger.warning("search_knowledge failed reason=%s", exc)
        return []


# ── learning logic ────────────────────────────────────────────────────────────

def _generate_queries(topic: str, context_hint: str) -> list[str]:
    """Generate 3 diverse search queries via Claude (or deterministic fallback)."""
    fallback = [
        f"{topic} tendances 2025",
        f"{topic} tutoriel guide pratique",
        f"{topic} actualités Afrique Cameroun",
    ]
    data = _llm.json_completion(
        system_prompt=(
            "Tu es un expert en recherche d'information. "
            "Génère 3 requêtes de recherche Google distinctes et optimisées pour le sujet donné. "
            "Retourne JSON: {\"queries\": [\"requête1\", \"requête2\", \"requête3\"]}. "
            "Les requêtes doivent couvrir : tendances, tutoriels/guides, actualités."
        ),
        user_prompt=f"Sujet : {topic}\nContexte : {context_hint}",
        fallback={"queries": fallback},
    )
    queries = data.get("queries", fallback)
    if not isinstance(queries, list) or len(queries) < 1:
        return fallback
    return [str(q) for q in queries[:3]]


def _relevance_score(topic: str, snippet: str) -> float:
    """Simple keyword overlap score 0–1."""
    topic_words = set(topic.lower().split())
    snippet_words = set(snippet.lower().split())
    if not topic_words:
        return 0.0
    overlap = topic_words & snippet_words
    return min(len(overlap) / len(topic_words), 1.0)


async def learn_from_web(topic: str, context_hint: str = "") -> list[str]:
    """
    Autonomously learn about a topic:
    1. Generate 3 search queries via Claude
    2. Execute searches
    3. Scrape 2 best URLs
    4. Summarise with Claude
    5. Save to Firestore
    Returns list of insight strings.
    """
    _logger.info("learning.start topic=%s", topic[:60])

    # 1. Generate queries
    queries = await asyncio.to_thread(_generate_queries, topic, context_hint)

    # 2. Search
    all_results = []
    for q in queries[:3]:
        results = await asyncio.to_thread(search, q, 3)
        all_results.extend(results)

    if not all_results:
        _logger.warning("learning.no_results topic=%s", topic[:60])
        return []

    # 3. Pick 2 best URLs by relevance score
    scored = sorted(
        all_results,
        key=lambda r: _relevance_score(topic, r.snippet),
        reverse=True,
    )
    top_results = scored[:2]
    sources = [r.url for r in top_results if r.url]

    scraped_texts = []
    for result in top_results:
        if result.url:
            page = await asyncio.to_thread(scrape, result.url)
            if page and page.content:
                scraped_texts.append(f"Source: {result.url}\n{page.content[:2000]}")

    # Fallback to snippets if scraping failed
    if not scraped_texts:
        scraped_texts = [f"{r.title}: {r.snippet}" for r in top_results]

    combined = "\n\n---\n\n".join(scraped_texts)

    # 4. Summarise
    fallback_summary = {
        "summary": f"Informations collectées sur : {topic}.",
        "insights": [f"Tendances actuelles sur {topic}", f"Ressources disponibles sur {topic}"],
        "relevance_score": 0.5,
    }
    data = _llm.json_completion(
        system_prompt=(
            "Tu es un expert en synthèse d'information pour une agence digitale africaine. "
            "Analyse le contenu fourni et extrais les insights clés, pratiques, et actionnables. "
            "Retourne JSON: {\"summary\": \"résumé court\", \"insights\": [\"insight1\", ...], \"relevance_score\": 0.0-1.0}. "
            "Maximum 5 insights. Chaque insight doit être une phrase actionnable en français."
        ),
        user_prompt=f"Sujet : {topic}\nContexte : {context_hint}\n\nContenu :\n{combined}",
        fallback=fallback_summary,
    )

    summary = str(data.get("summary", fallback_summary["summary"]))
    insights = data.get("insights", fallback_summary["insights"])
    if not isinstance(insights, list):
        insights = [str(insights)]
    insights = [str(i) for i in insights[:5]]
    score = float(data.get("relevance_score", 0.5))

    # 5. Save
    await asyncio.to_thread(_save_knowledge, topic, summary, insights, sources, context_hint, score)
    _logger.info("learning.done topic=%s insights=%d", topic[:60], len(insights))

    return insights
