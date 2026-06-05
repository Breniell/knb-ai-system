"""
Agent self-training engine.

Each agent has a curriculum of topics it should master.
Training cycle:
  learn_from_web(topic) → summarise → save to Firestore agentKnowledge/{agentName}/topics/{key}

On every task execution (via BaseAgent.__init_subclass__ wrap):
  get_agent_knowledge(agent_name, task_title) → inject into memory_snippets
"""

import asyncio
from datetime import datetime, timezone

from app.core.firebase import get_firestore_client
from app.core.logging import get_logger

_logger = get_logger("agent-trainer")
_COLLECTION = "agentKnowledge"
_STALE_HOURS = 48

# ── Curriculums ──────────────────────────────────────────────────────────────
# Each agent has 5 core topics to always research and master.

AGENT_CURRICULUMS: dict[str, list[str]] = {
    "DevFrontendAgent": [
        "React 19 server components hooks nouveautés 2025",
        "Next.js 15 App Router SSR performance SEO",
        "TypeScript 5 strict type safety best practices",
        "Tailwind CSS 4 composants accessibilité WCAG",
        "Core Web Vitals LCP FID CLS optimisation web performance",
    ],
    "DevBackendAgent": [
        "Node.js 22 LTS API REST architecture best practices 2025",
        "Prisma ORM PostgreSQL migrations requêtes optimisées",
        "JWT OAuth2 authentification sécurité backend",
        "Docker déploiement conteneurs production Node",
        "WebSocket temps réel Socket.io scalabilité",
    ],
    "DevMobileAgent": [
        "React Native 0.75 Expo SDK 52 nouveautés performance",
        "React Native navigation Expo Router tabs stacks",
        "Optimisation listes FlatList React Native performance",
        "Mobile Money API MTN MoMo Orange Money intégration",
        "PWA progressive web app vs application native comparaison",
    ],
    "ArchitecteAgent": [
        "Architecture microservices monolithe modulaire 2025",
        "Design patterns SOLID Clean Architecture DDD",
        "Scalabilité haute disponibilité systèmes distribués",
        "Sécurité architecture OWASP Top 10 2025",
        "Infrastructure cloud Vercel Render Firebase coût performance",
    ],
    "QAAgent": [
        "Tests automatisés Playwright Cypress end-to-end 2025",
        "Test driven development TDD BDD Jest Vitest",
        "CI/CD GitHub Actions pipeline tests qualité",
        "Tests performance charge Artillery k6 benchmarks",
        "Accessibilité audit WCAG 2.2 outils automatisés",
    ],
    "DevOpsAgent": [
        "GitHub Actions CI/CD pipeline déploiement automatique",
        "Docker Compose production secrets management",
        "Monitoring logs Grafana Prometheus alertes",
        "Sécurité DevSecOps SAST DAST scanning",
        "Render Vercel Railway déploiement gratuit configuration",
    ],
    "DesignerUXUIAgent": [
        "Design system Figma composants tokens réutilisables",
        "UX research interviews tests utilisateurs méthodes",
        "Accessibilité WCAG contraste couleurs inclusion",
        "Mobile first responsive design patterns 2025",
        "Onboarding utilisateur conversion rétention UX",
    ],
    "DesignerGraphiqueAgent": [
        "Identité visuelle logo branding Afrique Cameroun tendances",
        "Tendances design graphique couleurs typographies 2025",
        "Typographie web variable fonts sélection Google Fonts",
        "Psychologie couleurs branding émotions palette",
        "Formats vectoriels SVG exportation production Figma",
    ],
    "MarketingAgent": [
        "Marketing digital PME Afrique Cameroun stratégie 2025",
        "SEO référencement naturel Google algorithme 2025",
        "Google Ads Meta Ads budget ROI PME Afrique",
        "Content marketing stratégie réseaux sociaux engagement",
        "Email marketing automation taux conversion CTR benchmark",
    ],
    "CommunityManagerAgent": [
        "Instagram Facebook TikTok stratégie engagement Afrique 2025",
        "WhatsApp Business catalogue marketing Cameroun",
        "Création contenu viral formats Reels Shorts tendances",
        "Community management crise communication gestion",
        "Calendrier éditorial planification publication outil",
    ],
    "CommercialAgent": [
        "Négociation commerciale BtoB BtoC techniques closing Afrique",
        "Tarification projets web mobile FCFA benchmarks marché",
        "Proposition commerciale pitch deck présentation client",
        "CRM pipeline commercial gestion prospects PME",
        "Paiement échelonné Mobile Money contrats Cameroun",
    ],
    "FinanceAgent": [
        "Comptabilité PME OHADA Cameroun obligations légales",
        "Facturation devis TVA taux Cameroun 2025",
        "Trésorerie gestion flux cash PME numérique",
        "Financement startup Cameroun investisseurs subventions",
        "Pricing services numériques rentabilité marges FCFA",
    ],
    "ChefDeProjetAgent": [
        "Méthode Agile Scrum sprint planning retrospective",
        "Planification projet WBS estimation charges livrables",
        "Gestion risques projets techniques mitigation",
        "Communication client stakeholder reporting projet",
        "Outils gestion projet Notion Trello Jira Linear comparaison",
    ],
    "RedacteurAgent": [
        "Copywriting conversion landing page CTA persuasion",
        "SEO rédaction articles blog mots-clés structure 2025",
        "Storytelling brand content narration marque Afrique",
        "Rédaction technique documentation API développeurs",
        "Newsletter email copywriting objet taux ouverture",
    ],
    "SupportClientAgent": [
        "Relation client satisfaction NPS CSAT mesure amélioration",
        "Gestion réclamations clients processus escalade",
        "Support technique helpdesk SLA ticketing best practices",
        "Onboarding formation client logiciel adoption",
        "Fidélisation client LTV rétention stratégies PME",
    ],
    "ReviewerAgent": [
        "Code review checklist qualité sécurité performance",
        "Audit technique dette technique refactoring stratégie",
        "Documentation technique standard OpenAPI Swagger",
        "Recette fonctionnelle test acceptance critères",
        "Lighthouse PageSpeed audit performance web score",
    ],
    "FrontendAgent": [
        "React TypeScript composants hooks bonnes pratiques",
        "Performance web optimisation bundle splitting lazy",
        "Accessibilité web WCAG sémantique HTML aria",
    ],
    "BackendAgent": [
        "Node.js API REST GraphQL architecture 2025",
        "PostgreSQL MongoDB indexation requêtes optimisation",
        "Sécurité backend injection SQL XSS validation",
    ],
}


# ── Knowledge read ────────────────────────────────────────────────────────────

def _topic_key(topic: str) -> str:
    return topic.lower().strip()[:80].replace(" ", "_")


async def get_agent_knowledge(agent_name: str, task_title: str, max_snippets: int = 6) -> list[str]:
    """Return the most relevant learned insights for an agent before it executes."""
    client = get_firestore_client()
    if client is None:
        return []
    try:
        def _fetch():
            return list(
                client.collection(_COLLECTION)
                .document(agent_name)
                .collection("topics")
                .limit(30)
                .stream()
            )

        docs = await asyncio.to_thread(_fetch)
        if not docs:
            return []

        task_words = set(task_title.lower().split())
        scored: list[tuple[int, list[str]]] = []
        for doc in docs:
            data = doc.to_dict()
            topic_words = set(data.get("topic", "").lower().split())
            overlap = len(task_words & topic_words)
            insights = data.get("insights", [])
            if insights:
                scored.append((overlap, insights))

        scored.sort(key=lambda x: x[0], reverse=True)
        result: list[str] = []
        for _, insights in scored[:3]:
            result.extend(insights[:2])
        return result[:max_snippets]
    except Exception as exc:
        _logger.debug("get_agent_knowledge failed agent=%s reason=%s", agent_name, exc)
        return []


# ── Knowledge write ───────────────────────────────────────────────────────────

async def _save_agent_topic(agent_name: str, topic: str, insights: list[str], sources: list[str]) -> None:
    client = get_firestore_client()
    if client is None:
        return
    key = _topic_key(topic)
    try:
        def _write():
            client.collection(_COLLECTION).document(agent_name).collection("topics").document(key).set({
                "topic": topic,
                "insights": insights,
                "sources": sources,
                "agentName": agent_name,
                "learnedAt": datetime.now(timezone.utc).timestamp(),
                "usageCount": 0,
            })
        await asyncio.to_thread(_write)
        _logger.info("knowledge.saved agent=%s topic=%s insights=%d", agent_name, topic[:50], len(insights))
    except Exception as exc:
        _logger.warning("save_agent_topic failed agent=%s topic=%s reason=%s", agent_name, topic[:40], exc)


async def _is_fresh(agent_name: str, topic: str) -> bool:
    """Return True if this topic was learned recently enough (< _STALE_HOURS)."""
    client = get_firestore_client()
    if client is None:
        return False
    key = _topic_key(topic)
    try:
        def _get():
            return client.collection(_COLLECTION).document(agent_name).collection("topics").document(key).get()
        doc = await asyncio.to_thread(_get)
        if not doc.exists:
            return False
        learned_at = doc.to_dict().get("learnedAt", 0)
        age_hours = (datetime.now(timezone.utc).timestamp() - learned_at) / 3600
        return age_hours < _STALE_HOURS
    except Exception:
        return False


# ── Training ──────────────────────────────────────────────────────────────────

async def train_agent(agent_name: str, force: bool = False) -> dict:
    """Train one agent on its curriculum. Skips topics already learned recently."""
    from app.tools.learning_engine import learn_from_web

    curriculum = AGENT_CURRICULUMS.get(agent_name, [])
    if not curriculum:
        return {"agent": agent_name, "skipped": True, "reason": "no curriculum"}

    _logger.info("training.start agent=%s topics=%d force=%s", agent_name, len(curriculum), force)
    results = []

    for topic in curriculum:
        if not force and await _is_fresh(agent_name, topic):
            results.append({"topic": topic, "ok": True, "cached": True})
            continue
        try:
            insights = await learn_from_web(topic, context_hint=agent_name)
            await _save_agent_topic(agent_name, topic, insights, [])
            results.append({"topic": topic, "insights": len(insights), "ok": True, "cached": False})
            await asyncio.sleep(1)  # avoid rate-limit bursts
        except Exception as exc:
            results.append({"topic": topic, "ok": False, "error": str(exc)})

    trained = sum(1 for r in results if r.get("ok") and not r.get("cached"))
    _logger.info("training.done agent=%s trained=%d cached=%d", agent_name,
                 trained, len(results) - trained)
    return {"agent": agent_name, "results": results, "ok": True}


async def run_global_training(agent_names: list[str] | None = None, force: bool = False) -> list[dict]:
    """Train all agents sequentially (one at a time to respect free-tier rate limits)."""
    names = agent_names or list(AGENT_CURRICULUMS.keys())
    reports = []
    for name in names:
        try:
            report = await train_agent(name, force=force)
            reports.append(report)
            await asyncio.sleep(2)
        except Exception as exc:
            reports.append({"agent": name, "ok": False, "error": str(exc)})
    return reports


# ── Status ────────────────────────────────────────────────────────────────────

async def get_training_status() -> list[dict]:
    """Return per-agent training status from Firestore."""
    client = get_firestore_client()
    if client is None:
        return [{"error": "Firestore non disponible"}]

    statuses = []
    for agent_name, curriculum in AGENT_CURRICULUMS.items():
        try:
            def _fetch(name=agent_name):
                return list(
                    client.collection(_COLLECTION)
                    .document(name)
                    .collection("topics")
                    .stream()
                )
            docs = await asyncio.to_thread(_fetch)
            entries = [d.to_dict() for d in docs]
            last_ts = max((e.get("learnedAt", 0) for e in entries), default=0)
            statuses.append({
                "agent": agent_name,
                "topics_learned": len(entries),
                "curriculum_size": len(curriculum),
                "completion_pct": round(len(entries) / len(curriculum) * 100) if curriculum else 0,
                "last_trained": datetime.fromtimestamp(last_ts, tz=timezone.utc).isoformat() if last_ts else None,
                "is_trained": len(entries) > 0,
            })
        except Exception as exc:
            statuses.append({"agent": agent_name, "error": str(exc)})
    return statuses
