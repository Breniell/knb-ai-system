"""
core/tools.py — Outils que les agents peuvent appeler EN COURS DE TÂCHE.

C'est le mécanisme central de l'autonomie : un agent peut décider, pendant
sa réflexion, de chercher sur le web, scraper une page, retrouver un artefact
produit par un autre agent, ou explorer sa base de connaissances Firestore.

Architecture inspirée du pattern ReAct (Reason + Act) :
  - Chaque outil a un nom, une description en français, un schéma d'arguments
  - L'agent reçoit la liste des outils dispos + des exemples d'usage
  - L'agent émet { "tool": "...", "args": {...} } dans son JSON
  - Le runtime exécute l'outil, retourne le résultat, et boucle

Tous les outils sont SAFE-BY-DEFAULT : ils retournent une erreur structurée
plutôt que de lever une exception, pour ne jamais casser la boucle agent.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable

from app.core.logging import get_logger

_logger = get_logger("agent-tools")


# ═══════════════════════════════════════════════════════════════════════════════
# Modèles
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class ToolResult:
    """Résultat normalisé d'un outil. ok=False signifie erreur récupérable."""
    ok: bool
    output: Any
    error: str = ""
    tool: str = ""

    def to_string(self, max_chars: int = 2000) -> str:
        """Formate le résultat pour ré-injection dans le contexte LLM."""
        if not self.ok:
            return f"[outil {self.tool} → ERREUR: {self.error}]"
        out = self.output
        if isinstance(out, (list, tuple)):
            text = "\n".join(f"- {item}" for item in out[:10])
        elif isinstance(out, dict):
            text = "\n".join(f"{k}: {str(v)[:200]}" for k, v in list(out.items())[:10])
        else:
            text = str(out)
        if len(text) > max_chars:
            text = text[:max_chars] + "…[tronqué]"
        return text


@dataclass
class ToolSpec:
    """Description d'un outil exposé à l'agent."""
    name: str
    description: str          # en français, ce que fait l'outil
    args_schema: str          # JSON schema textuel pour le prompt LLM
    handler: Callable[..., Awaitable[ToolResult]]
    example: str = ""         # exemple d'appel JSON pour few-shot


# ═══════════════════════════════════════════════════════════════════════════════
# Handlers d'outils
# ═══════════════════════════════════════════════════════════════════════════════

async def _tool_web_search(query: str, max_results: int = 5) -> ToolResult:
    """Recherche web (Brave si configuré, sinon DuckDuckGo)."""
    try:
        from app.tools.web_search import search
        results = await asyncio.to_thread(search, query, max_results)
        if not results:
            return ToolResult(ok=True, output=[], tool="web_search",
                              error="aucun résultat")
        formatted = [
            f"{r.title} — {r.snippet[:200]} ({r.url})" for r in results[:max_results]
        ]
        return ToolResult(ok=True, output=formatted, tool="web_search")
    except Exception as e:
        return ToolResult(ok=False, output=None, error=str(e)[:200], tool="web_search")


async def _tool_web_scrape(url: str) -> ToolResult:
    """Extrait le texte propre d'une URL (avec cache 24h)."""
    if not url or not url.startswith(("http://", "https://")):
        return ToolResult(ok=False, output=None,
                          error="URL invalide", tool="web_scrape")
    try:
        from app.tools.web_scraper import scrape
        page = await asyncio.to_thread(scrape, url)
        if page is None or not page.content:
            return ToolResult(ok=True, output="",
                              error="page vide", tool="web_scrape")
        return ToolResult(
            ok=True,
            output={"title": page.title, "content": page.content[:3000]},
            tool="web_scrape",
        )
    except Exception as e:
        return ToolResult(ok=False, output=None, error=str(e)[:200], tool="web_scrape")


async def _tool_recall_knowledge(agent_name: str, topic: str) -> ToolResult:
    """
    Recherche dans la base de connaissances de l'agent.
    Utilise learning_engine_v2 (Firestore enrichi par l'apprentissage autonome)
    avec fallback vers l'ancien moteur si Firestore n'est pas configuré.
    """
    try:
        from app.tools.learning_engine_v2 import get_agent_knowledge_v2
        snippets = await get_agent_knowledge_v2(agent_name, topic, max_snippets=8)
        if snippets:
            return ToolResult(ok=True, output=snippets, tool="recall_knowledge")
    except Exception:
        pass
    # Fallback vers agent_trainer original
    try:
        from app.tools.agent_trainer import get_agent_knowledge
        snippets = await get_agent_knowledge(agent_name, topic, max_snippets=6)
        return ToolResult(
            ok=True,
            output=snippets or ["[aucune connaissance trouvée pour ce sujet]"],
            tool="recall_knowledge",
        )
    except Exception as e:
        return ToolResult(ok=False, output=None, error=str(e)[:200],
                          tool="recall_knowledge")


async def _tool_learn_topic(topic: str, context_hint: str = "") -> ToolResult:
    """
    Apprend un sujet à la volée.
    Cherche d'abord dans Firestore (cache learning_engine_v2), puis fait une
    recherche web + synthèse si rien n'est trouvé.
    """
    # 1. Cache Firestore enrichi (v2)
    try:
        from app.tools.learning_engine_v2 import get_stored_knowledge
        agent_name = context_hint or "general"
        cached = await get_stored_knowledge(agent_name, topic)
        if cached and cached.get("insights"):
            return ToolResult(ok=True, output=cached["insights"][:10], tool="learn_topic")
    except Exception:
        pass

    # 2. Cache learning_engine original
    try:
        from app.tools.learning_engine import get_cached_knowledge
        cached = get_cached_knowledge(topic)
        if cached:
            return ToolResult(ok=True, output=cached, tool="learn_topic")
    except Exception:
        pass

    # 3. Recherche web + synthèse
    try:
        from app.tools.learning_engine import learn_from_web
        insights = await learn_from_web(topic, context_hint=context_hint)
        return ToolResult(
            ok=True,
            output=insights or ["[aucun insight extrait pour ce sujet]"],
            tool="learn_topic",
        )
    except Exception as e:
        return ToolResult(ok=False, output=None, error=str(e)[:200], tool="learn_topic")


# ═══════════════════════════════════════════════════════════════════════════════
# Catalogue
# ═══════════════════════════════════════════════════════════════════════════════



async def _tool_search_past_work(
    query: str,
    agent: str = "",
    max_results: int = 3,
) -> ToolResult:
    """
    Recherche dans les livrables RÉELS produits lors de workflows passés.
    Utilise la mémoire vectorielle Qdrant (ou Firestore en fallback).
    Retourne des extraits de code, devis, designs, plans passés pertinents.
    """
    try:
        from app.memory.vector_memory import VectorMemory
        vm = VectorMemory()
        results = vm.search_past_work(
            query=query,
            limit=max_results,
            agent=agent or None,
        )
        if not results:
            return ToolResult(ok=True, output=["Aucun travail similaire trouvé dans la mémoire."],
                              tool="search_past_work")
        formatted = []
        for r in results:
            score_pct = int(r["score"] * 100)
            title = r.get("title", "Sans titre")
            agent_name = r.get("agent", "?")
            preview = r.get("content", "")[:600]
            formatted.append(
                f"[Similarité {score_pct}% — {agent_name} — {title}]\n{preview}"
            )
        return ToolResult(ok=True, output=formatted, tool="search_past_work")
    except Exception as e:
        return ToolResult(ok=False, output=None, error=str(e)[:200],
                          tool="search_past_work")

def build_default_tools(agent_name: str) -> dict[str, ToolSpec]:
    """Retourne le catalogue d'outils pour un agent donné."""
    return {
        "web_search": ToolSpec(
            name="web_search",
            description=(
                "Recherche sur le web. Utilise pour trouver des informations "
                "récentes, des tarifs marché, des best practices, des "
                "concurrents, des sources fraîches. Retourne une liste "
                "de titres + extraits + URLs."
            ),
            args_schema='{"query": "string", "max_results": "int (1-5)"}',
            handler=_tool_web_search,
            example='{"tool":"web_search","args":{"query":"tarif Shopify dev Cameroun 2025","max_results":4}}',
        ),
        "web_scrape": ToolSpec(
            name="web_scrape",
            description=(
                "Récupère le contenu textuel propre d'une URL (article, doc, "
                "page). Utilise après web_search pour aller au fond d'une "
                "source pertinente."
            ),
            args_schema='{"url": "https://..."}',
            handler=_tool_web_scrape,
            example='{"tool":"web_scrape","args":{"url":"https://example.com/article"}}',
        ),
        "recall_knowledge": ToolSpec(
            name="recall_knowledge",
            description=(
                "Cherche dans TA base de connaissances personnelle (insights "
                "que tu as déjà étudiés et stockés). Utilise en début de tâche "
                "pour mobiliser ton expertise."
            ),
            args_schema='{"topic": "string"}',
            handler=lambda topic: _tool_recall_knowledge(agent_name, topic),
            example='{"tool":"recall_knowledge","args":{"topic":"tarification site vitrine FCFA"}}',
        ),
        "learn_topic": ToolSpec(
            name="learn_topic",
            description=(
                "Apprends un nouveau sujet : déclenche une recherche web + "
                "synthèse, et stocke les insights dans Firestore pour les "
                "tâches futures. Utilise quand recall_knowledge ne donne "
                "rien et que le sujet est nouveau pour toi."
            ),
            args_schema='{"topic": "string", "context_hint": "string"}',
            handler=lambda topic, context_hint="": _tool_learn_topic(topic, context_hint),
            example='{"tool":"learn_topic","args":{"topic":"PWA offline first React Native","context_hint":"DevMobileAgent"}}',
        ),
        "search_past_work": ToolSpec(
            name="search_past_work",
            description=(
                "Cherche dans les livrables RÉELS produits lors de projets passés "
                "(code, devis, plans, designs). Utilise en début de tâche pour "
                "t'appuyer sur ce qu'on a déjà fait plutôt que de repartir de zéro. "
                "Exemple : retrouver un devis similaire pour l'adapter, ou un composant "
                "React qu'on a déjà codé."
            ),
            args_schema='{"query": "string", "agent": "string (optionnel)", "max_results": "int 1-5"}',
            handler=lambda query, agent="", max_results=3: _tool_search_past_work(query, agent, max_results),
            example='{"tool":"search_past_work","args":{"query":"devis site vitrine PME Yaoundé","max_results":3}}',
        ),
    }


def render_tools_for_prompt(tools: dict[str, ToolSpec]) -> str:
    """Formate la liste des outils pour injection dans un system prompt."""
    lines = ["OUTILS À TA DISPOSITION (appelle-les via JSON quand pertinent) :\n"]
    for spec in tools.values():
        lines.append(f"• {spec.name} — {spec.description}")
        lines.append(f"  args : {spec.args_schema}")
        if spec.example:
            lines.append(f"  exemple : {spec.example}")
        lines.append("")
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
# Exécuteur
# ═══════════════════════════════════════════════════════════════════════════════

async def execute_tool_call(
    tool_calls: list[dict[str, Any]],
    tools: dict[str, ToolSpec],
    max_concurrent: int = 3,
) -> list[ToolResult]:
    """
    Exécute une liste d'appels d'outils en parallèle (limité).
    Chaque appel doit avoir la forme {"tool": "name", "args": {...}}.
    """
    if not tool_calls:
        return []

    semaphore = asyncio.Semaphore(max_concurrent)

    async def _run(call: dict[str, Any]) -> ToolResult:
        async with semaphore:
            name = call.get("tool", "")
            args = call.get("args", {}) or {}
            if name not in tools:
                return ToolResult(
                    ok=False, output=None,
                    error=f"outil inconnu : {name}", tool=name,
                )
            try:
                spec = tools[name]
                _logger.info("tool_call agent=? tool=%s args=%s",
                             name, str(args)[:120])
                # args est un dict, on déballe pour le handler
                result = await spec.handler(**args) if isinstance(args, dict) else \
                         await spec.handler(args)
                if not isinstance(result, ToolResult):
                    result = ToolResult(ok=True, output=result, tool=name)
                if not result.tool:
                    result.tool = name
                return result
            except TypeError as e:
                return ToolResult(
                    ok=False, output=None,
                    error=f"arguments invalides : {str(e)[:140]}", tool=name,
                )
            except Exception as e:
                _logger.warning("tool_call failed tool=%s error=%s",
                                name, str(e)[:160])
                return ToolResult(ok=False, output=None,
                                  error=str(e)[:200], tool=name)

    return await asyncio.gather(*(_run(c) for c in tool_calls))


# ═══════════════════════════════════════════════════════════════════════════════
# Trace d'exécution (pour observabilité par tâche)
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class AgentTrace:
    """Trace des actions d'un agent pour debug et journalisation."""
    agent_name: str
    task_title: str
    iterations: int = 0
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    self_critiques: list[str] = field(default_factory=list)
    final_score: float = 0.0

    def add_tool(self, call: dict[str, Any], result: ToolResult) -> None:
        self.tool_calls.append({
            "tool": call.get("tool", ""),
            "args": call.get("args", {}),
            "ok": result.ok,
            "error": result.error,
            "output_preview": result.to_string(max_chars=300),
        })

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent": self.agent_name,
            "task": self.task_title,
            "iterations": self.iterations,
            "tool_calls": self.tool_calls,
            "self_critiques": self.self_critiques,
            "final_score": self.final_score,
        }
