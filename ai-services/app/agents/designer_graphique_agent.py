"""
agents/designergraphiqueagent_agent.py — Wrapper KnbAgent (v3.1).
"""
from __future__ import annotations
from typing import Any
from app.agents.base import KnbAgent
from app.agents._senior_prompts import SENIOR_PROMPTS
from app.models import ExecutionContext, SubTask


class DesignerGraphiqueAgent(KnbAgent):
    name = "DesignerGraphiqueAgent"
    specialty = "Identité visuelle, logo, charte graphique, branding PME"
    emoji = "🖌️"
    _system_prompt = SENIOR_PROMPTS.get("DesignerGraphiqueAgent", "")

    def _fallback_response(self, task: SubTask, context: ExecutionContext) -> dict[str, Any]:
        return {
            "summary": "Brief de design graphique complet avec direction créative définie, palette de couleurs + couple typographique recommandé, et déclinaisons d'usage (web, print, réseaux sociaux).",
            "artifacts": [{'type': 'brand_brief', 'title': 'Brief identité visuelle KNB', 'content': '## DIRECTION CRÉATIVE\nPositionnement : Tech professionnel + ancrage camerounais + innovation\nTonalité visuelle : sobre, moderne, confiance\nInspiration : tech SaaS (Stripe, Linear) × chaud africain\n\n## PALETTE RECOMMANDÉE\nPrimaire    : #0A0F1E (Marine profond — sérieux, tech)\nSecondaire  : #0EA5E9 (Sky blue — dynamisme, digital)\nAccent      : #F97316 (Orange chaud — énergie, Afrique)\nNeutre clair: #F8FAFC\nNeutre sombre: #1E293B\n\n## TYPOGRAPHIE\nTitre   : Sora (géométrique, moderne, lisible petit écran)\nCorps   : Inter (standard tech, excellent hinting)\nUsage alternance : Sora Bold pour H1-H2, Inter Regular pour corps\n\n## SYMBOLE / LOGO\nPiste 1 : Monogramme K stylisé avec un pixel ou un bracket { }\nPiste 2 : Ligature KNB avec accent géométrique (triangle, hexagone)\nPiste 3 : Wordmark clean SORA BOLD tout caps\n→ Tester les 3 pistes en N&B avant couleur\n\n## FORMATS À LIVRER\nSVG vectoriel / PNG 512px / PNG 64px favicon / JPG fond blanc\nCouverture Facebook 820×312 / Post Instagram 1080×1080 / Carte de visite'}],
            "followups": ['Avez-vous un logo existant à faire évoluer ou on part de zéro ?', 'Quels concurrents directs ou inspirations visuelles (locaux ou internationaux) ?', 'Formats prioritaires : digital seulement ou print aussi (cartes, rollup) ?'],
            "score": 0.78,
        }
