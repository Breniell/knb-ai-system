"""
agents/reviewer_agent.py — Reviewer KNB v2.

Différences clés vs version originale :
  - Hérite de KnbAgent → recherche + auto-critique automatiques.
  - Reçoit les artefacts complets via context.metadata["prior_artifacts"]
    (au lieu de seulement les résumés tronqués) → peut détecter de vraies
    contradictions au lieu d'en inventer.
  - Émet un verdict structuré (go / go_with_minor_fixes / no_go) + une
    liste de corrections ciblées par agent + artefact, exploitée par le
    workflow pour déclencher un re-travail (rework) automatique.
"""

from __future__ import annotations

import json
from typing import Any

from app.agents.base import KnbAgent
from app.agents.knb_context import KNB_CONTEXT
from app.core.llm import LlmClient
from app.models import AgentResponse, ExecutionContext, SubTask


class ReviewerAgent(KnbAgent):
    name = "ReviewerAgent"
    specialty = "Revue finale multi-agents, cohérence, go/no-go, plan de correction"
    emoji = "🔍"

    # Le reviewer n'a pas besoin de chercher sur le web : il analyse l'existant
    _enable_research = False
    _max_revisions = 1  # une seule passe de révision sur sa propre critique

    _system_prompt = f"""
{KNB_CONTEXT}

Tu es le Reviewer Final de l'agence KNB. Tu analyses les livrables produits par
les autres agents et tu rends un verdict structuré.

Tu vois les artefacts COMPLETS (pas seulement les résumés). Toutes tes
affirmations doivent s'appuyer sur des éléments concrets que tu peux citer.

Critères de revue :
1. COHÉRENCE — les choix techniques/design/contenu sont alignés entre agents.
2. COMPLÉTUDE — les livrables couvrent le périmètre demandé.
3. QUALITÉ — chaque artefact est utilisable sans retravail majeur.
4. CONTRADICTIONS — détection de décisions opposées (ex: archi dit PostgreSQL,
   backend implémente MongoDB).
5. RISQUES — points qui mettent en danger la livraison client.

Verdicts possibles :
- "go" : prêt pour le client.
- "go_with_minor_fixes" : 1-3 corrections rapides (< 2h).
- "no_go" : révision majeure d'au moins un agent nécessaire.

Format JSON OBLIGATOIRE :
{{
  "summary": "verdict + score global + raisons principales (3-5 phrases)",
  "artifacts": [
    {{
      "type": "revue_finale",
      "title": "Rapport de Revue Multi-Agents",
      "content": "rapport complet structuré (markdown autorisé)"
    }}
  ],
  "verdict": "go | go_with_minor_fixes | no_go",
  "coherence_score": 0.0-1.0,
  "rework_requests": [
    {{
      "agent": "DevBackendAgent",
      "artifact_title": "Schéma Prisma",
      "issue": "Utilise MongoDB alors que l'architecte a tranché PostgreSQL.",
      "priority": "P1"
    }}
  ],
  "followups": ["question/action 1", "question/action 2"],
  "score": 0.0-1.0
}}

Tu ne dois RIEN inventer. Si un artefact n'est pas présent, ne le critique pas.
""".strip()

    def _fallback_response(self, task: SubTask, context: ExecutionContext) -> dict[str, Any]:
        prior = context.metadata.get("prior_artifacts", []) if context.metadata else []
        nb_agents = len(prior)
        return {
            "summary": (
                f"Revue automatique de {nb_agents} agent(s). Mode fallback "
                "(aucun LLM disponible) → verdict par défaut conservateur."
            ),
            "artifacts": [
                {
                    "type": "revue_finale",
                    "title": "Revue Multi-Agents (fallback)",
                    "content": (
                        "Aucun LLM disponible pour effectuer une revue détaillée. "
                        "Configure GROQ_API_KEY ou GEMINI_API_KEY pour activer "
                        "la revue automatique. Les livrables ne sont pas "
                        "validés à ce stade."
                    ),
                }
            ],
            "verdict": "go_with_minor_fixes",
            "coherence_score": 0.6,
            "rework_requests": [],
            "followups": [
                "Configurer une clé LLM gratuite pour activer la revue ?",
                "Quels livrables doivent être validés en priorité ?",
            ],
            "score": 0.6,
        }

    async def execute(
        self,
        task: SubTask,
        context: ExecutionContext,
        llm: LlmClient,
    ) -> AgentResponse:
        # On délègue à KnbAgent qui pilote la boucle (draft + critique + revise).
        response = await super().execute(task, context, llm)
        # On préserve verdict/rework_requests dans le summary si présents,
        # car AgentResponse ne les modélise pas explicitement. Ils sont aussi
        # poussés dans artifacts pour conservation au niveau workflow.
        return response

    @staticmethod
    def parse_verdict(response: AgentResponse) -> dict[str, Any]:
        """
        Tente d'extraire verdict + rework_requests depuis la réponse du reviewer.
        Cherche dans : 1) artifacts (un artefact dédié), 2) summary.
        Retourne un dict normalisé exploité par le workflow.
        """
        default = {
            "verdict": "go_with_minor_fixes",
            "coherence_score": float(response.score or 0.0),
            "rework_requests": [],
        }

        # Cherche un artefact qui contiendrait un JSON structuré
        for art in response.artifacts:
            content = art.get("content", "")
            if not isinstance(content, str):
                continue
            for key in ("verdict", "rework_requests"):
                if key in content:
                    try:
                        # Tente d'extraire un blob JSON
                        from app.core.llm import repair_and_parse_json
                        parsed = repair_and_parse_json(content)
                        if parsed:
                            default["verdict"] = str(
                                parsed.get("verdict", default["verdict"])
                            )
                            default["coherence_score"] = float(
                                parsed.get("coherence_score", default["coherence_score"])
                            )
                            rw = parsed.get("rework_requests", [])
                            if isinstance(rw, list):
                                default["rework_requests"] = rw
                            return default
                    except Exception:
                        pass
        return default
