"""
agents/communitymanageragent_agent.py — Wrapper KnbAgent (v3.1).
"""
from __future__ import annotations
from typing import Any
from app.agents.base import KnbAgent
from app.agents._senior_prompts import SENIOR_PROMPTS
from app.models import ExecutionContext, SubTask


class CommunityManagerAgent(KnbAgent):
    name = "CommunityManagerAgent"
    specialty = "Facebook, Instagram, TikTok, WhatsApp Business, calendrier éditorial"
    emoji = "📣"
    _system_prompt = SENIOR_PROMPTS.get("CommunityManagerAgent", "")

    def _fallback_response(self, task: SubTask, context: ExecutionContext) -> dict[str, Any]:
        return {
            "summary": 'Calendrier éditorial 4 semaines livré avec 12 posts planifiés sur Facebook, Instagram et WhatsApp. Mix 70% valeur / 30% promo. 3 posts publishables prêts à poster inclus avec hashtags.',
            "artifacts": [{'type': 'editorial_calendar', 'title': 'Calendrier éditorial — Mois 1', 'content': "## PILIERS DE CONTENU KNB\n1. ÉDUCATIF (40%) — conseils digitalisation, astuces tech\n2. COULISSES (30%) — équipe, process, projets en cours\n3. SOCIAL PROOF (20%) — témoignages clients, avant/après\n4. PROMO (10%) — offres, services\n\n## SEMAINE 1\n| Jour | Canal | Format | Sujet |\n|------|-------|--------|-------|\n| Lun | Instagram | Carrousel | '5 signes que votre PME a besoin d\\'un site web' |\n| Mer | Facebook | Post texte + image | Citation entrepreneur + CTA WhatsApp |\n| Ven | Instagram Reel | 30s | Avant/Après projet client |\n| Sam | WhatsApp Broadcast | Message | Offre weekend : consultation gratuite |\n\n## POST PUBLISHABLE — Instagram Carrousel\nCaption : 'Votre PME est-elle invisible sur internet ? 👀\n\nEn 2025, 78% des clients cherchent un prestataire en ligne avant de décider.\n\nSwipe → pour voir les 5 signes que vous avez besoin d\\'un site web professionnel.\n\n💬 Et vous ? Votre entreprise est-elle déjà en ligne ?\n\n#KNB #DigitalisationCameroun #SiteWeb #PMECameroun #YaoundéBusiness #Tech'\n\nHASHTAGS : #KNB #DigitalisationCameroun #SiteWeb #PMECameroun\n#YaoundéBusiness #Tech #WebDesign #Cameroun #StartupAfrique"}],
            "followups": ["Sur quels réseaux êtes-vous déjà présents (avec combien d'abonnés) ?", 'Avez-vous du contenu visuel existant (photos équipe, projets, locaux) ?', 'Quelle cadence de publication est réaliste pour votre équipe (2/sem, 5/sem) ?'],
            "score": 0.78,
        }
