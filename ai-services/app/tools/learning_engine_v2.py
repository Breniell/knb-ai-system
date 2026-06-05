"""
tools/learning_engine_v2.py — Moteur d'apprentissage autonome avancé.

Ce module enrichit l'original learning_engine.py avec :
  1. Apprentissage ciblé depuis les curricula de learning_resources.py
     (docs officielles, formations gratuites, certifications).
  2. Synthèse structurée : pas de dump brut — le LLM extrait des "insights
     actionnables" qu'il peut réutiliser dans ses tâches.
  3. Stockage Firestore stratifié :
     - raw_page : contenu brut de la ressource (TTL 7j)
     - synthesis : insights extraits (TTL selon freshness_hours)
     - mastery_level : score de maîtrise du topic par l'agent (0.0-1.0)
  4. Support des sources multi-format : articles, docs, cours (Coursera-audit,
     HubSpot Academy, Google Digital Garage).
  5. Résumé de session pour le scheduler : combien de sujets appris,
     lesquels ont échoué, durée.

L'original learning_engine.py reste utilisé pour le cache et les snippets.
Ce module est appelé par agent_trainer_v2.py, lui-même déclenché par
le scheduler.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("learning-engine-v2")


# ═══════════════════════════════════════════════════════════════════════════════
# Extraction et synthèse
# ═══════════════════════════════════════════════════════════════════════════════

async def scrape_url_safe(url: str, timeout: int = 15) -> str | None:
    """Scrape une URL avec fallback gracieux. Retourne None si échec."""
    try:
        from app.tools.web_scraper import scrape
        page = await asyncio.to_thread(scrape, url)
        if page and page.content:
            return f"[SOURCE: {url}]\n[TITRE: {page.title}]\n{page.content[:4000]}"
        return None
    except Exception as e:
        logger.warning("scrape_failed url=%s error=%s", url, str(e)[:100])
        return None


async def synthesize_learning(
    agent_name: str,
    topic: str,
    raw_content: str,
    synthesis_prompt: str,
    llm: Any,
) -> list[str]:
    """
    Demande au LLM de synthétiser le contenu brut en insights actionnables.
    Retourne une liste de bullet points utilisables dans des prompts d'agents.
    """
    system = (
        f"Tu es l'assistant d'apprentissage de {agent_name}, expert senior. "
        "Tu lis du contenu de formation et tu extrais les insights ACTIONNABLES "
        "— des connaissances concrètes que l'agent peut utiliser immédiatement "
        "dans ses tâches. Pas de résumé générique : des faits précis, des règles "
        "empiriques, des exemples de code ou de chiffres si disponibles.\n\n"
        "Format de réponse : une liste JSON de strings, 5 à 10 items.\n"
        "Exemple : [\"PostgreSQL : toujours créer un index composite sur (user_id, status) "
        "pour les requêtes filtrées par user + status\", ...]"
    )
    user = (
        f"Sujet : {topic}\n"
        f"Instruction d'extraction : {synthesis_prompt}\n\n"
        f"CONTENU À ANALYSER :\n{raw_content[:5000]}"
    )
    fallback = [f"[{topic}] documentation consultée mais non synthétisée (LLM indisponible)"]

    from app.core.llm import repair_and_parse_json
    raw = llm.text_completion(system, user, temperature=0.2)
    if not raw:
        return fallback

    # Tente de parser une liste JSON
    parsed = repair_and_parse_json(raw)
    if isinstance(parsed, dict) and "data" in parsed:
        data = parsed["data"]
        if isinstance(data, list):
            return [str(i) for i in data if str(i).strip()]
    if isinstance(parsed, list):
        return [str(i) for i in parsed if str(i).strip()]

    # Tente d'extraire une liste plain text (lignes commençant par - ou •)
    lines = []
    for line in raw.split("\n"):
        line = line.strip()
        if line.startswith(("-", "•", "*", "›")):
            clean = line.lstrip("-•*›").strip()
            if len(clean) > 15:
                lines.append(clean)
    if lines:
        return lines[:10]

    # Fallback : texte brut tronqué
    return [raw[:500]]


# ═══════════════════════════════════════════════════════════════════════════════
# Stockage Firestore
# ═══════════════════════════════════════════════════════════════════════════════

def _firestore_key(agent_name: str, topic: str) -> str:
    return f"agentKnowledge/{agent_name}/topics/{topic.replace('-', '_')}"


async def get_stored_knowledge(agent_name: str, topic: str) -> dict[str, Any] | None:
    """Récupère la connaissance stockée pour un topic (avec TTL)."""
    try:
        from app.core.firebase import get_firestore_client
        from app.tools.learning_resources import ALL_CURRICULA
        db = get_firestore_client()
        if not db:
            return None
        doc = db.document(_firestore_key(agent_name, topic)).get()
        if not doc.exists:
            return None
        data = doc.to_dict()

        # Vérifie la fraîcheur
        curriculum = ALL_CURRICULA.get(agent_name)
        freshness_hours = 168
        if curriculum:
            for resource in curriculum.resources:
                if resource.topic == topic:
                    freshness_hours = resource.freshness_hours
                    break

        updated_at = data.get("updated_at")
        if updated_at:
            age_hours = (
                datetime.now(timezone.utc) - updated_at
            ).total_seconds() / 3600
            if age_hours > freshness_hours:
                return None  # obsolète
        return data
    except Exception as e:
        logger.debug("get_stored_knowledge failed: %s", e)
        return None


async def store_knowledge(
    agent_name: str,
    topic: str,
    insights: list[str],
    sources: list[str],
    mastery_level: float = 0.5,
) -> bool:
    """Stocke les insights dans Firestore."""
    try:
        from app.core.firebase import get_firestore_client
        db = get_firestore_client()
        if not db:
            return False
        doc_data = {
            "agent": agent_name,
            "topic": topic,
            "insights": insights[:20],
            "sources": sources,
            "mastery_level": mastery_level,
            "updated_at": datetime.now(timezone.utc),
            "insight_count": len(insights),
        }
        db.document(_firestore_key(agent_name, topic)).set(doc_data)
        return True
    except Exception as e:
        logger.warning("store_knowledge failed: %s", e)
        return False


async def get_relevant_insights(
    agent_name: str,
    task_description: str,
    max_insights: int = 12,
) -> list[str]:
    """
    Récupère les insights les plus pertinents pour une tâche donnée.
    Concatène les topics dont les mots-clés se retrouvent dans la description.
    """
    try:
        from app.core.firebase import get_firestore_client
        db = get_firestore_client()
        if not db:
            return []

        # Récupère tous les topics de l'agent
        collection = db.collection(f"agentKnowledge/{agent_name}/topics")
        docs = collection.stream()

        task_lower = task_description.lower()
        all_insights: list[tuple[float, str]] = []

        for doc in docs:
            data = doc.to_dict()
            if not data:
                continue
            topic = data.get("topic", "")
            insights = data.get("insights", [])
            mastery = float(data.get("mastery_level", 0.5))

            # Score de pertinence simple : mots-clés du topic dans la tâche
            topic_words = topic.replace("-", " ").replace("_", " ").lower().split()
            relevance = sum(1 for w in topic_words if w in task_lower and len(w) > 3)
            if relevance > 0 or mastery > 0.8:
                for insight in insights:
                    all_insights.append((relevance + mastery, insight))

        # Tri par score décroissant, dédup, limite
        all_insights.sort(key=lambda x: x[0], reverse=True)
        seen: set[str] = set()
        result: list[str] = []
        for _, insight in all_insights:
            key = hashlib.md5(insight[:80].encode()).hexdigest()
            if key not in seen:
                seen.add(key)
                result.append(insight)
                if len(result) >= max_insights:
                    break
        return result
    except Exception as e:
        logger.debug("get_relevant_insights failed: %s", e)
        return []


# ═══════════════════════════════════════════════════════════════════════════════
# Formation d'un agent sur son curriculum
# ═══════════════════════════════════════════════════════════════════════════════

async def train_agent_on_curriculum(
    agent_name: str,
    llm: Any,
    force: bool = False,
    max_topics: int = 5,
) -> dict[str, Any]:
    """
    Lance la formation d'un agent sur N topics de son curriculum.
    Scrape les URLs, synthétise avec le LLM, stocke dans Firestore.
    Retourne un rapport de session.
    """
    from app.tools.learning_resources import get_curriculum

    curriculum = get_curriculum(agent_name)
    if not curriculum:
        return {"agent": agent_name, "ok": False, "error": "pas de curriculum défini"}

    report = {
        "agent": agent_name,
        "ok": True,
        "trained_topics": [],
        "skipped_topics": [],
        "failed_topics": [],
        "insights_total": 0,
    }

    topics_to_train = curriculum.resources[:max_topics]

    for resource in topics_to_train:
        # Vérifie si ce topic est déjà frais
        if not force:
            existing = await get_stored_knowledge(agent_name, resource.topic)
            if existing:
                report["skipped_topics"].append(resource.topic)
                logger.debug("train_skip agent=%s topic=%s (fresh)", agent_name, resource.topic)
                continue

        # Scrape les URLs
        raw_parts: list[str] = []
        for url in resource.urls[:3]:  # max 3 URLs par topic
            content = await scrape_url_safe(url)
            if content:
                raw_parts.append(content)
            await asyncio.sleep(1)  # Respecte les serveurs

        if not raw_parts:
            # Pas de scrape possible → recherche web de secours
            try:
                from app.tools.web_search import search
                results = await asyncio.to_thread(search, resource.topic, 4)
                if results:
                    raw_parts = [
                        f"[WEB SEARCH RESULT]\n{r.title}\n{r.snippet}"
                        for r in results
                    ]
            except Exception:
                pass

        if not raw_parts:
            report["failed_topics"].append({
                "topic": resource.topic,
                "reason": "aucune source accessible",
            })
            continue

        # Synthétise
        combined = "\n\n---\n\n".join(raw_parts[:3])
        try:
            insights = await synthesize_learning(
                agent_name=agent_name,
                topic=resource.topic,
                raw_content=combined,
                synthesis_prompt=resource.synthesis_prompt,
                llm=llm,
            )
        except Exception as e:
            logger.warning("synthesize failed agent=%s topic=%s: %s",
                           agent_name, resource.topic, e)
            report["failed_topics"].append({"topic": resource.topic, "reason": str(e)[:100]})
            continue

        # Stocke
        mastery = min(1.0, 0.4 + 0.1 * len(insights))
        stored = await store_knowledge(
            agent_name=agent_name,
            topic=resource.topic,
            insights=insights,
            sources=resource.urls,
            mastery_level=mastery,
        )
        if stored:
            report["trained_topics"].append(resource.topic)
            report["insights_total"] += len(insights)
            logger.info(
                "train_ok agent=%s topic=%s insights=%d mastery=%.2f",
                agent_name, resource.topic, len(insights), mastery,
            )
        else:
            report["failed_topics"].append({"topic": resource.topic, "reason": "store failed"})

        await asyncio.sleep(2)  # Pause entre topics

    return report


# ═══════════════════════════════════════════════════════════════════════════════
# Récupération rapide pour le recall tool
# ═══════════════════════════════════════════════════════════════════════════════

async def get_agent_knowledge_v2(
    agent_name: str,
    task: str,
    max_snippets: int = 8,
) -> list[str]:
    """
    Appelé par core/tools.py → recall_knowledge.
    Retourne les insights Firestore + les snippets learning_engine original.
    """
    insights = await get_relevant_insights(agent_name, task, max_insights=max_snippets)

    # Complète avec l'ancien moteur si Firestore vide
    if len(insights) < 3:
        try:
            from app.tools.learning_engine import get_cached_knowledge
            legacy = get_cached_knowledge(task) or []
            insights.extend([i for i in legacy if i not in insights])
        except Exception:
            pass

    return insights[:max_snippets]
