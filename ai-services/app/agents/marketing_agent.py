"""
agents/marketingagent_agent.py — Wrapper KnbAgent (v3.1).
"""
from __future__ import annotations
from typing import Any
from app.agents.base import KnbAgent
from app.agents._senior_prompts import SENIOR_PROMPTS
from app.models import ExecutionContext, SubTask


class MarketingAgent(KnbAgent):
    name = "MarketingAgent"
    specialty = "Growth marketing PME, Meta Ads, Google Ads, SEO, funnel conversion"
    emoji = "📈"
    _system_prompt = SENIOR_PROMPTS.get("MarketingAgent", "")

    def _fallback_response(self, task: SubTask, context: ExecutionContext) -> dict[str, Any]:
        return {
            "summary": 'Stratégie marketing 90 jours livrée : mix Meta Ads + SEO local + WhatsApp Business. Budget recommandé 75 000 FCFA/mois pour 15-25 leads qualifiés. KPIs et tableau de suivi inclus.',
            "artifacts": [{'type': 'marketing_strategy', 'title': 'Stratégie marketing 90 jours — KNB', 'content': '## OBJECTIF\nGénérer 15-25 leads qualifiés/mois pour KNB via digital.\n\n## PERSONAS CIBLES\n1. Antoine, 35 ans, gérant PME Yaoundé, cherche à digitaliser son activité\n2. Fatima, 28 ans, entrepreneur startup, veut une app mobile MVP\n\n## MIX CANAUX (Budget 75 000 FCFA/mois)\n\n| Canal | Budget FCFA | Leads cibles | CPL cible |\n|-------|------------|--------------|----------|\n| Meta Ads (FB/IG) | 40 000 | 10-15 | 3 000 |\n| SEO + contenu | 0 (temps) | 3-5 (long terme) | 0 |\n| WhatsApp Broadcast | 0 | 2-5 | 0 |\n| Référral client | 5 000 | 3-5 | 1 000 |\n| Google Ads Search | 30 000 | 5-8 | 5 000 |\n\n## PHASE 1 — Mois 1 : Fondations\n- Setup Meta Pixel + GA4\n- Créer 3 audiences custom (visiteurs site, base email, LLA)\n- Lancer 1 campagne Meta notoriété (10 000 FCFA test)\n- Activer WhatsApp Business (catalog, messages auto)\n\n## KPI DE PILOTAGE HEBDO\n- Leads : objectif 4/semaine\n- CPL réel vs cible\n- Taux de conversion landing : cible 3%+\n- Engagement réseaux : reach + taux engagement'}],
            "followups": ['Quel budget mensuel réaliste pour commencer (minimum viable : 50 000 FCFA) ?', 'Le site web actuel a-t-il Google Analytics et Meta Pixel installés ?', 'Existe-t-il une base de contacts (email ou WhatsApp) à activer ?'],
            "score": 0.78,
        }
