"""
agents/master_orchestrator_agent.py — Coordination centrale.

Cet agent peut être assigné par le planner pour produire un compte-rendu de
coordination en haut de workflow (synthèse exécutive, dépendances, jalons).
Refactoré pour respecter le contrat AgentResponse (artifacts = list[dict]).
"""

from __future__ import annotations

from typing import Any

from app.agents.base import KnbAgent
from app.agents.knb_context import KNB_CONTEXT
from app.models import ExecutionContext, SubTask


class MasterOrchestratorAgent(KnbAgent):
    name = "MasterOrchestratorAgent"
    specialty = "Coordination workflow, suivi d'exécution, vue exécutive"
    emoji = "🎯"

    _enable_research = False  # ne cherche pas sur le web, synthétise du contexte

    _system_prompt = f"""
{KNB_CONTEXT}

Tu es le coordinateur central de l'agence. Tu produis une vue exécutive
synthétique d'un projet ou d'un workflow : objectif, périmètre, équipe
mobilisée, dépendances, jalons, risques principaux.

Tu n'écris pas de code ni de design. Tu donnes la photo d'ensemble qu'un
fondateur peut lire en 30 secondes pour décider.

Format JSON OBLIGATOIRE :
{{
  "summary": "vue exécutive 3-5 phrases",
  "artifacts": [
    {{"type": "coordination_brief", "title": "...", "content": "..."}}
  ],
  "followups": ["..."],
  "score": 0.0-1.0
}}
""".strip()

    def _fallback_response(self, task: SubTask, context: ExecutionContext) -> dict[str, Any]:
        return {
            "summary": (
                f"Coordination de : {task.title}. Pipeline standard KNB en "
                "5 phases (cadrage → design → dev → recette → mise en ligne) "
                "avec checkpoints client à chaque fin de phase."
            ),
            "artifacts": [
                {
                    "type": "coordination_brief",
                    "title": "Brief de coordination",
                    "content": (
                        "OBJECTIF\n"
                        f"Livrer : {task.title}\n\n"
                        "ÉQUIPE MOBILISÉE\n"
                        "- ArchitecteAgent (cadrage technique)\n"
                        "- DesignerUXUIAgent (wireframes)\n"
                        "- DevFrontendAgent + DevBackendAgent (dev)\n"
                        "- QAAgent (tests)\n"
                        "- DevOpsAgent (mise en ligne)\n"
                        "- ChefDeProjetAgent (coordination)\n\n"
                        "JALONS CLÉS\n"
                        "J+7  : cahier des charges validé\n"
                        "J+14 : maquettes validées\n"
                        "J+45 : version alpha interne\n"
                        "J+60 : recette client\n"
                        "J+70 : mise en ligne\n\n"
                        "RISQUES PRINCIPAUX\n"
                        "1. Validation client en retard → planifier 3 j ouvrés de buffer\n"
                        "2. Scope creep → demandes de changement formalisées\n"
                        "3. Dépendances paiement/SMS → tester en sandbox dès J+30"
                    ),
                }
            ],
            "followups": [
                "Quelle est la date butoir contractuelle ?",
                "Y a-t-il des dépendances externes (API tierces, validations) ?",
                "Quel est le budget total alloué (FCFA) ?",
            ],
            "score": 0.78,
        }
