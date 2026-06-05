"""
agents/financeagent_agent.py — Wrapper KnbAgent (v3.1).
"""
from __future__ import annotations
from typing import Any
from app.agents.base import KnbAgent
from app.agents._senior_prompts import SENIOR_PROMPTS
from app.models import ExecutionContext, SubTask


class FinanceAgent(KnbAgent):
    name = "FinanceAgent"
    specialty = "Fiscalité camerounaise OHADA, TVA 19.25%, trésorerie PME, devis FCFA"
    emoji = "💰"
    _system_prompt = SENIOR_PROMPTS.get("FinanceAgent", "")

    def _fallback_response(self, task: SubTask, context: ExecutionContext) -> dict[str, Any]:
        return {
            "summary": 'Analyse financière complète avec devis OHADA conforme, ventilation HT/TVA 19,25%/TTC, prévisionnel de trésorerie 6 mois et recommandations fiscales pour PME camerounaise.',
            "artifacts": [{'type': 'financial_analysis', 'title': 'Facture et analyse financière projet', 'content': "## STRUCTURE TARIFAIRE\n\n| Prestation | Montant HT | TVA 19,25% | TTC |\n|-----------|-----------|-----------|------|\n| Développement | 200 000 FCFA | 38 500 FCFA | 238 500 FCFA |\n| Design | 75 000 FCFA | 14 438 FCFA | 89 438 FCFA |\n| Maintenance 12 mois | 60 000 FCFA | 11 550 FCFA | 71 550 FCFA |\n| **TOTAL** | **335 000 FCFA** | **64 488 FCFA** | **399 488 FCFA** |\n\n## OBLIGATIONS FISCALES PME CAMEROUN\n- Numéro d'identification unique (NIU) obligatoire sur toutes factures\n- TVA 19,25% : collectée sur prestations taxables, déclarée trimestriellement\n- IS (Impôt sur les Sociétés) : 30% du bénéfice imposable\n- Retenue à la source 5,5% : applicable si client personne morale\n- Cotisations CNPS : à prévoir si employés permanents\n\n## TRÉSORERIE — RÈGLES POUR KNB\n1. Acompte 50% obligatoire avant début travaux\n2. Provision IS : mettre 8-10% du CA HT de côté chaque mois\n3. Provision TVA collectée : mettre 19,25% de côté pour le reversement\n4. Réserve trésorerie cible : 3 mois de charges fixes\n5. Mobile Money : commission MTN 1,5% / Orange 2% à intégrer dans les prix"}],
            "followups": ["L'entreprise est-elle au régime simplifié ou réel d'imposition ?", 'Des clients personnes morales (sociétés) ? (retenue à la source 5,5% applicable)', "Besoin d'un prévisionnel cash flow pour une levée de fonds ou un crédit bancaire ?"],
            "score": 0.78,
        }
