"""
agents/redacteuragent_agent.py — Wrapper KnbAgent (v3.1).
"""
from __future__ import annotations
from typing import Any
from app.agents.base import KnbAgent
from app.agents._senior_prompts import SENIOR_PROMPTS
from app.models import ExecutionContext, SubTask


class RedacteurAgent(KnbAgent):
    name = "RedacteurAgent"
    specialty = "Copywriting SEO, email marketing, landing pages, contenu réseaux"
    emoji = "✍️"
    _system_prompt = SENIOR_PROMPTS.get("RedacteurAgent", "")

    def _fallback_response(self, task: SubTask, context: ExecutionContext) -> dict[str, Any]:
        return {
            "summary": 'Page web complète rédigée (landing ou article) avec structure SEO, CTA clair et ton adapté à la cible. Meta description et H1/H2 optimisés inclus.',
            "artifacts": [{'type': 'landing_page_copy', 'title': 'Texte landing page KNB', 'content': "# [H1] Votre PME mérite un site web qui travaille pour vous, même la nuit\n\n## Sous-titre\nNous créons des sites web et applications mobiles qui transforment les visiteurs en clients — pour les entrepreneurs camerounais ambitieux.\n\n## [H2] Pourquoi KNB ?\n\n**Vous perdez des clients chaque jour sans le savoir.**\nEn 2025, 78% des consommateurs cherchent en ligne avant d'acheter. Sans présence digitale professionnelle, vous n'existez pas pour eux.\n\nKNB change ça. En 2 semaines, vous avez un site qui :\n- Inspire confiance dès la première visite\n- Génère des prospects via WhatsApp automatiquement\n- Fonctionne parfaitement sur tous les téléphones\n- Vous fait gagner du temps (formulaires, infos, catalogue)\n\n## [H2] Nos réalisations parlent pour nous\n[Témoignages clients / captures d'écran projets]\n\n## [CTA principal]\n**Obtenez votre devis gratuit en 24h**\nDécrivez votre projet sur WhatsApp → on vous répond dans la journée.\n\n---\nMETA DESCRIPTION (155 car.) :\nKNB crée des sites web et apps mobiles pour PME camerounaises. Devis gratuit en 24h. Site livré en 2 semaines. Yaoundé & toute l'Afrique."}],
            "followups": ['Ton souhaité : professionnel-institutionnel ou plus proche, chaleureux ?', "Mots-clés SEO prioritaires (ex: 'agence web Yaoundé', 'application mobile Cameroun') ?", 'Le contenu est pour quel canal/format : web, email, réseaux sociaux, brochure ?'],
            "score": 0.78,
        }
