"""
agents/chefdeprojetagent_agent.py — Wrapper KnbAgent (v3.1).
"""
from __future__ import annotations
from typing import Any
from app.agents.base import KnbAgent
from app.agents._senior_prompts import SENIOR_PROMPTS
from app.models import ExecutionContext, SubTask


class ChefDeProjetAgent(KnbAgent):
    name = "ChefDeProjetAgent"
    specialty = "Agile/Scrum PME, roadmaps, gestion risques RAID, coordination équipes"
    emoji = "📋"
    _system_prompt = SENIOR_PROMPTS.get("ChefDeProjetAgent", "")

    def _fallback_response(self, task: SubTask, context: ExecutionContext) -> dict[str, Any]:
        return {
            "summary": 'Cahier des charges priorisé MoSCoW + roadmap 3 phases avec jalons clients + matrice de risques RAID avec 5 risques identifiés. Plan de communication WhatsApp/email inclus.',
            "artifacts": [{'type': 'project_charter', 'title': 'Cahier des charges — Priorisation MoSCoW', 'content': "## MUST HAVE (livrable phase 1 — obligatoire)\n- Authentification (email + Google)\n- Dashboard principal (liste + création)\n- Formulaire de contact / commande WhatsApp\n- Design responsive mobile\n- Hébergement + nom de domaine\n\n## SHOULD HAVE (phase 1 si temps, sinon phase 2)\n- Notifications email automatiques\n- Interface admin de gestion de contenu\n- Intégration Google Analytics\n\n## COULD HAVE (phase 2)\n- Paiement en ligne MTN MoMo\n- Espace client avec historique\n- Blog / section actualités\n\n## WON'T HAVE (hors périmètre phase 1)\n- Application mobile native\n- Système de facturation intégré\n- Multi-langue\n\n## ROADMAP\nPhase 1 — Cadrage (J0-J7) : validation charte, maquettes, validation client\nPhase 2 — Dev (J8-J35) : sprints 1 sem, démo client chaque vendredi\nPhase 3 — Recette + Go-Live (J36-J45) : tests, corrections, mise en ligne\n\n## TOP 3 RISQUES\nR1 : Retard validation maquettes (prob. haute) → buffer 3j, SLA contractuel\nR2 : Scope creep demandes hors cahier (prob. haute) → change request process\nR3 : Indispo hébergement jour J (prob. faible) → backup Railway/Vercel"}],
            "followups": ['Quelle est la date de mise en ligne contractuelle ? (oriente le planning backward)', 'Le client a-t-il déjà validé un budget et signé un acompte ?', "L'équipe de dev est disponible à 100% sur ce projet ou partagée ?"],
            "score": 0.78,
        }
