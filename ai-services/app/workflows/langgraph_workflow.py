"""
workflows/langgraph_workflow.py — Workflow KNB v2.

Différences clés vs v1 :
  1. Planner ADAPTATIF : choisit les agents selon le type de demande (dev,
     marketing, finance, support, créa…), au lieu de forcer un plan dev fixe.
  2. Transmission des ARTEFACTS complets entre agents (pas seulement summary
     tronqué). C'est ce qui permet au reviewer de réellement vérifier la
     cohérence, et au backend dev de partir du modèle de l'architecte.
  3. Boucle REWORK : si le ReviewerAgent renvoie un verdict "no_go" ou
     "go_with_minor_fixes" avec des `rework_requests` ciblées, on re-route
     vers les agents concernés (max N passes de rework globales).
  4. Garde-fous : limite d'itérations totales, retry par tâche, et journal
     d'exécution exhaustif (timeline).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, TypedDict
from uuid import uuid4

from langgraph.graph import END, StateGraph

from app.core.llm import LlmClient
from app.core.logging import get_logger
from app.models import ExecutionContext, SubTask
from app.orchestrator.agent_registry import AgentRegistry

_logger = get_logger("workflow")

# Tous les agents que le planner peut assigner
_ALL_AGENTS = {
    "FrontendAgent", "BackendAgent", "QAAgent", "DevOpsAgent", "ReviewerAgent",
    "CommercialAgent", "MarketingAgent", "CommunityManagerAgent",
    "ArchitecteAgent", "DevFrontendAgent", "DevBackendAgent", "DevMobileAgent",
    "DesignerUXUIAgent", "DesignerGraphiqueAgent", "RedacteurAgent",
    "ChefDeProjetAgent", "SupportClientAgent", "FinanceAgent",
    "MasterOrchestratorAgent",
}

# Garde-fous globaux
_MAX_TOTAL_STEPS = 30      # nb total max d'exécutions d'agent par workflow
_MAX_REWORK_ROUNDS = 2     # nb max de rounds de re-travail déclenchés par reviewer
_RETRY_PER_TASK = 3        # tentatives par tâche en cas d'erreur


class WorkflowState(TypedDict):
    request: str
    context: ExecutionContext
    plan: list[dict[str, Any]]
    queue: list[dict[str, Any]]
    responses: list[dict[str, Any]]
    timeline: list[dict[str, Any]]
    retry_map: dict[str, int]
    errors: list[str]
    total_steps: int
    rework_rounds: int


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ─── Heuristique de routage (pour quand le LLM ne planifie pas) ───────────────

_KEYWORDS_AGENTS: list[tuple[tuple[str, ...], list[str]]] = [
    # (mots-clés, agents pertinents par ordre de priorité)
    (("devis", "facture", "tarif", "prix", "fcfa", "tva", "ohada", "budget"),
        ["FinanceAgent", "CommercialAgent", "ReviewerAgent"]),
    (("prospection", "client", "vente", "lead", "closing", "proposition commerciale"),
        ["CommercialAgent", "MarketingAgent", "ReviewerAgent"]),
    (("marketing", "campagne", "ads", "seo", "leads", "stratégie digitale"),
        ["MarketingAgent", "RedacteurAgent", "ReviewerAgent"]),
    (("post", "facebook", "instagram", "tiktok", "linkedin", "réseaux sociaux", "community"),
        ["CommunityManagerAgent", "RedacteurAgent", "DesignerGraphiqueAgent", "ReviewerAgent"]),
    (("article", "blog", "copywriting", "newsletter", "rédaction"),
        ["RedacteurAgent", "MarketingAgent", "ReviewerAgent"]),
    (("logo", "identité", "charte graphique", "branding"),
        ["DesignerGraphiqueAgent", "RedacteurAgent", "ReviewerAgent"]),
    (("ux", "ui", "wireframe", "maquette", "design system", "figma"),
        ["DesignerUXUIAgent", "DesignerGraphiqueAgent", "ReviewerAgent"]),
    (("mobile", "react native", "expo", "android", "ios", "app"),
        ["ArchitecteAgent", "DesignerUXUIAgent", "DevMobileAgent",
         "QAAgent", "ReviewerAgent"]),
    (("backend", "api", "prisma", "postgres", "node", "express", "auth"),
        ["ArchitecteAgent", "DevBackendAgent", "QAAgent", "ReviewerAgent"]),
    (("frontend", "react", "next.js", "tailwind", "composant", "ui"),
        ["DesignerUXUIAgent", "DevFrontendAgent", "QAAgent", "ReviewerAgent"]),
    (("déploiement", "docker", "vercel", "railway", "ci/cd", "github actions", "devops"),
        ["DevOpsAgent", "QAAgent", "ReviewerAgent"]),
    (("recette", "test", "qa", "playwright", "checklist"),
        ["QAAgent", "ReviewerAgent"]),
    (("support", "réclamation", "onboarding", "nps", "fidélisation"),
        ["SupportClientAgent", "ReviewerAgent"]),
    (("planning", "roadmap", "agile", "scrum", "cahier des charges", "risques"),
        ["ChefDeProjetAgent", "ArchitecteAgent", "ReviewerAgent"]),
    # Projet complet (par défaut si rien ne matche un thème spécifique)
    (("site web", "application", "plateforme", "saas", "projet"),
        ["ChefDeProjetAgent", "ArchitecteAgent", "DesignerUXUIAgent",
         "DevFrontendAgent", "DevBackendAgent", "QAAgent", "DevOpsAgent",
         "ReviewerAgent"]),
]


def _heuristic_plan(request: str) -> list[dict[str, Any]]:
    """Plan de secours déterministe basé sur les mots-clés de la requête."""
    text = request.lower()
    matched: list[str] = []
    for keywords, agents in _KEYWORDS_AGENTS:
        if any(k in text for k in keywords):
            matched.extend(agents)
    if not matched:
        # Plan minimal : juste un chef de projet et un reviewer pour cadrer
        matched = ["ChefDeProjetAgent", "ReviewerAgent"]

    # Dédup en préservant l'ordre
    seen: set[str] = set()
    ordered: list[str] = []
    for a in matched:
        if a not in seen:
            seen.add(a)
            ordered.append(a)

    plan = []
    for idx, agent in enumerate(ordered):
        priority = 1 if agent in ("ArchitecteAgent", "ChefDeProjetAgent") else 2
        if agent == "ReviewerAgent":
            priority = 9  # reviewer toujours en dernier
        plan.append({
            "id": str(uuid4()),
            "title": f"Contribution {agent}",
            "description": f"Produire le livrable {agent} pour : {request[:200]}",
            "assigned_agent": agent,
            "priority": priority,
        })
    return plan


# ─── Construction du workflow ─────────────────────────────────────────────────

def build_workflow(registry: AgentRegistry, llm: LlmClient):
    graph = StateGraph(WorkflowState)

    # ── Normalisation du plan ────────────────────────────────────────────────

    def normalize_plan(
        raw_plan: Any, fallback_plan: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        if not isinstance(raw_plan, list) or not raw_plan:
            return fallback_plan
        normalized: list[dict[str, Any]] = []
        seen_agents: set[str] = set()
        for item in raw_plan:
            if not isinstance(item, dict):
                continue
            title = str(item.get("title") or "Tâche").strip()
            description = str(item.get("description") or title).strip()
            assigned = str(item.get("assigned_agent") or "").strip()
            if assigned not in _ALL_AGENTS:
                continue
            try:
                priority = int(item.get("priority") or 2)
            except (TypeError, ValueError):
                priority = 2
            normalized.append({
                "id": str(item.get("id") or uuid4()),
                "title": title,
                "description": description,
                "assigned_agent": assigned,
                "priority": priority,
            })
            seen_agents.add(assigned)

        # On garantit toujours la présence du ReviewerAgent en fin
        if "ReviewerAgent" not in seen_agents:
            normalized.append({
                "id": str(uuid4()),
                "title": "Revue finale multi-agents",
                "description": "Vérifier cohérence et qualité des livrables.",
                "assigned_agent": "ReviewerAgent",
                "priority": 9,
            })
        return normalized or fallback_plan

    # ── Node : planner ───────────────────────────────────────────────────────

    async def planner(state: WorkflowState) -> WorkflowState:
        # Initialise les compteurs si l'orchestrator ne les a pas fournis
        state.setdefault("total_steps", 0)
        state.setdefault("rework_rounds", 0)
        state.setdefault("retry_map", {})
        state.setdefault("errors", [])
        state.setdefault("responses", [])
        state.setdefault("timeline", [])

        request = state["request"]
        agents_desc = (
            "ChefDeProjetAgent (roadmap, sprints, risques), "
            "ArchitecteAgent (architecture, stack), "
            "DevFrontendAgent (React/Next.js), DevBackendAgent (Node/Prisma), "
            "DevMobileAgent (React Native/Expo), DesignerUXUIAgent (wireframes), "
            "DesignerGraphiqueAgent (logo/branding), RedacteurAgent (copywriting), "
            "QAAgent (tests), DevOpsAgent (CI/CD, déploiement), "
            "CommercialAgent (devis, propositions), MarketingAgent (stratégie digitale), "
            "CommunityManagerAgent (réseaux sociaux), FinanceAgent (FCFA, OHADA), "
            "SupportClientAgent (relation client), "
            "ReviewerAgent (revue finale — toujours en dernier)"
        )
        fallback_plan = _heuristic_plan(request)

        system = (
            "Tu es le planificateur principal de KNB. À partir de la demande client, "
            "tu choisis les agents pertinents (pas tous, juste ceux qui apportent "
            "de la valeur) et tu décris leur sous-tâche.\n\n"
            f"Agents disponibles : {agents_desc}.\n\n"
            "RÈGLES :\n"
            "- Ne planifie QUE des agents qui ont un livrable à produire.\n"
            "- Ne fais pas de dev/architecture pour une demande purement marketing.\n"
            "- Ne fais pas de marketing pour une demande purement technique.\n"
            "- Termine TOUJOURS par ReviewerAgent (priority 9).\n"
            "- 2-6 agents max selon la complexité.\n\n"
            "Retourne JSON : {\"plan\": [{\"id\":\"...\", \"title\":\"...\", "
            "\"description\":\"...\", \"assigned_agent\":\"NomAgent\", \"priority\":1-9}, ...]}"
        )
        user = (
            f"Demande du client : {request}\n"
            f"Mémoire contexte : {state['context'].memory_snippets[:5]}"
        )
        data = llm.json_completion(
            system, user, fallback={"plan": fallback_plan}, max_retries=1,
        )
        plan = normalize_plan(data.get("plan", fallback_plan), fallback_plan)
        state["plan"] = plan
        state["queue"] = sorted(plan, key=lambda x: int(x.get("priority", 2)))
        now = _now_iso()
        state["timeline"].append({
            "node": "planner",
            "success": True,
            "started_at": now,
            "ended_at": now,
            "details": {
                "plan_size": len(plan),
                "agents": [p["assigned_agent"] for p in plan],
            },
        })
        _logger.info(
            "planner workflow=%s agents=%s",
            state["context"].workflow_id,
            [p["assigned_agent"] for p in plan],
        )
        return state

    # ── Exécution d'un agent avec contexte enrichi ───────────────────────────

    async def run_agent(agent_name: str, state: WorkflowState) -> WorkflowState:
        state["total_steps"] = state.get("total_steps", 0) + 1
        state.setdefault("rework_rounds", 0)
        state.setdefault("retry_map", {})
        state.setdefault("errors", [])
        if state["total_steps"] > _MAX_TOTAL_STEPS:
            state["errors"].append(
                f"workflow stoppé : limite de {_MAX_TOTAL_STEPS} étapes atteinte"
            )
            state["queue"] = []
            return state

        target = next(
            (item for item in state["queue"] if item.get("assigned_agent") == agent_name),
            None,
        )
        if not target:
            return state
        state["queue"] = [it for it in state["queue"] if it.get("id") != target.get("id")]
        subtask = SubTask.model_validate(target)
        start = _now_iso()

        # Construction d'un contexte ENRICHI avec :
        # - les artefacts complets des agents précédents
        # - les memory snippets accumulés
        prior_artifacts = [
            {"agent": r["agent"], "artifacts": r.get("artifacts", [])}
            for r in state["responses"]
            if r.get("artifacts")
        ]
        previous_summaries = [
            f"[{r['agent']}] {r['summary'][:300]}" for r in state["responses"]
        ]

        enriched_context = ExecutionContext(
            workflow_id=state["context"].workflow_id,
            project_id=state["context"].project_id,
            task_id=state["context"].task_id,
            user_id=state["context"].user_id,
            memory_snippets=list(state["context"].memory_snippets) + previous_summaries,
            metadata={
                **(state["context"].metadata or {}),
                "prior_artifacts": prior_artifacts,
            },
        )

        try:
            agent = registry.get(agent_name)
            response = await agent.execute(subtask, enriched_context, llm)
            response_dump = response.model_dump()
            state["responses"].append(response_dump)
            state["timeline"].append({
                "node": agent_name,
                "success": True,
                "started_at": start,
                "ended_at": _now_iso(),
                "details": {
                    "task": subtask.title,
                    "score": response.score,
                    "artifacts_count": len(response.artifacts),
                },
            })
            _logger.info(
                "agent_done workflow=%s agent=%s score=%.2f artifacts=%d",
                state["context"].workflow_id, agent_name, response.score,
                len(response.artifacts),
            )

            # Si c'est le reviewer, on inspecte le verdict pour décider d'un rework
            if agent_name == "ReviewerAgent":
                await _maybe_trigger_rework(state, response_dump)

        except Exception as exc:
            key = subtask.id
            retries = state["retry_map"].get(key, 0) + 1
            state["retry_map"][key] = retries
            if retries < _RETRY_PER_TASK:
                state["queue"].append(target)
                _logger.warning(
                    "agent_retry workflow=%s agent=%s attempt=%d/%d error=%s",
                    state["context"].workflow_id, agent_name, retries,
                    _RETRY_PER_TASK, str(exc)[:140],
                )
            else:
                state["errors"].append(
                    f"{agent_name} failed pour {subtask.id} après {retries} essais : {exc}"
                )
                _logger.error(
                    "agent_failed_final workflow=%s agent=%s error=%s",
                    state["context"].workflow_id, agent_name, str(exc)[:200],
                )
            state["timeline"].append({
                "node": agent_name,
                "success": False,
                "started_at": start,
                "ended_at": _now_iso(),
                "details": {
                    "error": str(exc)[:300],
                    "retries": retries,
                },
            })
        return state

    async def _maybe_trigger_rework(
        state: WorkflowState, reviewer_response: dict[str, Any],
    ) -> None:
        """Si le reviewer demande du rework, on re-injecte des tâches ciblées."""
        if state["rework_rounds"] >= _MAX_REWORK_ROUNDS:
            return

        # Parser le verdict
        try:
            from app.agents.reviewer_agent import ReviewerAgent
            from app.models import AgentResponse as _AR
            verdict_info = ReviewerAgent.parse_verdict(
                _AR.model_validate(reviewer_response)
            )
        except Exception:
            verdict_info = {"verdict": "go", "rework_requests": []}

        verdict = verdict_info.get("verdict", "go")
        rework_requests = verdict_info.get("rework_requests", [])
        if verdict == "go" or not rework_requests:
            return

        state["rework_rounds"] += 1
        added = 0
        for req in rework_requests[:5]:  # max 5 reworks par round
            agent = str(req.get("agent", "")).strip()
            if agent not in _ALL_AGENTS or agent == "ReviewerAgent":
                continue
            issue = str(req.get("issue", "Correction demandée par le reviewer."))
            artifact_title = str(req.get("artifact_title", ""))
            new_task = {
                "id": str(uuid4()),
                "title": f"REWORK : {artifact_title or agent}",
                "description": (
                    f"Le ReviewerAgent a demandé une correction : {issue} "
                    f"Refais le livrable concerné en t'appuyant sur les "
                    f"artefacts des autres agents pour assurer la cohérence."
                ),
                "assigned_agent": agent,
                "priority": 5,
                "_rework": True,
            }
            state["queue"].insert(0, new_task)
            state["plan"].append(new_task)
            added += 1

        # On replanifie aussi le reviewer pour valider le rework
        if added > 0:
            state["queue"].append({
                "id": str(uuid4()),
                "title": "Revue post-rework",
                "description": "Vérifier que les corrections ont bien été appliquées.",
                "assigned_agent": "ReviewerAgent",
                "priority": 9,
                "_rework": True,
            })
            now = _now_iso()
            state["timeline"].append({
                "node": "rework_triggered",
                "success": True,
                "started_at": now,
                "ended_at": now,
                "details": {
                    "round": state["rework_rounds"],
                    "agents": [r.get("agent") for r in rework_requests[:added]],
                },
            })
            _logger.info(
                "rework_triggered workflow=%s round=%d agents=%s",
                state["context"].workflow_id, state["rework_rounds"],
                [r.get("agent") for r in rework_requests[:added]],
            )

    # ── Map node-name → agent-name ───────────────────────────────────────────

    _NODE_MAP = {
        "frontend": "FrontendAgent",
        "backend": "BackendAgent",
        "qa": "QAAgent",
        "devops": "DevOpsAgent",
        "reviewer": "ReviewerAgent",
        "commercial": "CommercialAgent",
        "marketing": "MarketingAgent",
        "community": "CommunityManagerAgent",
        "architecte": "ArchitecteAgent",
        "dev_frontend": "DevFrontendAgent",
        "dev_backend": "DevBackendAgent",
        "dev_mobile": "DevMobileAgent",
        "ux_ui": "DesignerUXUIAgent",
        "graphique": "DesignerGraphiqueAgent",
        "redacteur": "RedacteurAgent",
        "chef_projet": "ChefDeProjetAgent",
        "support": "SupportClientAgent",
        "finance": "FinanceAgent",
        "master": "MasterOrchestratorAgent",
    }
    _AGENT_TO_NODE = {v: k for k, v in _NODE_MAP.items()}

    def make_node(agent_name: str):
        async def node(state: WorkflowState) -> WorkflowState:
            return await run_agent(agent_name, state)
        node.__name__ = f"{agent_name.lower()}_node"
        return node

    def route(state: WorkflowState) -> str:
        if not state.get("queue"):
            return END
        if state.get("total_steps", 0) >= _MAX_TOTAL_STEPS:
            return END
        next_agent = state["queue"][0].get("assigned_agent", "ReviewerAgent")
        return _AGENT_TO_NODE.get(next_agent, "reviewer")

    # ── Assemblage du graphe ─────────────────────────────────────────────────

    graph.add_node("planner", planner)
    for node_name, agent_name in _NODE_MAP.items():
        graph.add_node(node_name, make_node(agent_name))

    graph.set_entry_point("planner")
    graph.add_conditional_edges("planner", route)
    for node_name in _NODE_MAP:
        graph.add_conditional_edges(node_name, route)

    return graph.compile()
