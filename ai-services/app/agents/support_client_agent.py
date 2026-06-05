"""
agents/supportclientagent_agent.py — Wrapper KnbAgent (v3.1).
"""
from __future__ import annotations
from typing import Any
from app.agents.base import KnbAgent
from app.agents._senior_prompts import SENIOR_PROMPTS
from app.models import ExecutionContext, SubTask


class SupportClientAgent(KnbAgent):
    name = "SupportClientAgent"
    specialty = "Customer success, onboarding clients, NPS/CSAT, WhatsApp support"
    emoji = "🎧"
    _system_prompt = SENIOR_PROMPTS.get("SupportClientAgent", "")

    def _fallback_response(self, task: SubTask, context: ExecutionContext) -> dict[str, Any]:
        return {
            "summary": "Process de support complet livré : scripts WhatsApp pour les 8 cas les plus fréquents, séquence d'onboarding client J0-J30, stratégie NPS trimestrielle. SLA définis : réponse < 2h WhatsApp, résolution < 48h.",
            "artifacts": [{'type': 'support_scripts', 'title': 'Scripts support WhatsApp — Top 8 cas', 'content': '## CAS 1 : Nouveau message client (bienvenue)\n"Bonjour [Prénom] ! 👋 Merci de nous contacter.\nJe suis [Votre prénom] de l\'équipe KNB.\nComment puis-je vous aider aujourd\'hui ?"\n\n## CAS 2 : Demande de devis\n"Avec plaisir ! Pour vous préparer un devis précis, pouvez-vous me dire :\n1. Le type de projet (site vitrine, e-commerce, app mobile ?)\n2. Le nombre de pages / fonctionnalités principales\n3. Votre délai souhaité\nJe vous envoie le devis sous 24h. ✅"\n\n## CAS 3 : Bug signalé\n"Merci de me le signaler, je comprends que c\'est frustrant.\nPouvez-vous m\'envoyer une capture d\'écran et me dire :\n- Sur quel appareil / navigateur ?\n- Ce que vous faisiez au moment du bug ?\nJe prends ça en main et vous reviens sous 4h. 🔧"\n\n## CAS 4 : Demande de modification post-livraison\n"Bien noté ! Cette modification [décrivez] est :\n✅ Dans le périmètre du contrat → je la planifie cette semaine\n📋 Hors périmètre → je vous prépare un devis complémentaire\nJe vous confirme ça d\'ici 2h."\n\n## SÉQUENCE ONBOARDING J0-J30\nJ0 : Message WhatsApp bienvenue + lien vers espace client\nJ3 : Appel 15 min \'tour de prise en main\'\nJ7 : Message check-in \'Comment ça se passe ?\'\nJ14 : Partage tutoriel vidéo fonctionnalité clé\nJ30 : Enquête NPS + proposition maintenance'}],
            "followups": ['Quel outil de support est déjà en place (WhatsApp Business, email, autre) ?', 'Combien de tickets de support par semaine en moyenne actuellement ?', 'Existe-t-il une FAQ client ou une base de connaissance publique ?'],
            "score": 0.78,
        }
