"""
agents/commercialagent_agent.py — Wrapper KnbAgent (v3.1).
"""
from __future__ import annotations
from typing import Any
from app.agents.base import KnbAgent
from app.agents._senior_prompts import SENIOR_PROMPTS
from app.models import ExecutionContext, SubTask


class CommercialAgent(KnbAgent):
    name = "CommercialAgent"
    specialty = "Vente B2B PME Cameroun, devis OHADA, closing WhatsApp, objections prix"
    emoji = "💼"
    _system_prompt = SENIOR_PROMPTS.get("CommercialAgent", "")

    def _fallback_response(self, task: SubTask, context: ExecutionContext) -> dict[str, Any]:
        return {
            "summary": "Devis complet prêt à envoyer avec ventilation HT/TVA/TTC, conditions de paiement en 2 fois, validité 30 jours. Email d'accompagnement bref inclus. Réponses aux 3 objections principales préparées.",
            "artifacts": [{'type': 'devis', 'title': 'Devis KNB — Site vitrine', 'content': "AGENCE KNB — DEVIS N° KNB-2025-001\nDate : [DATE] | Validité : 30 jours\nNIU : [VOTRE NIU]\n\nCLIENT : [NOM CLIENT]\nContact : [EMAIL / WhatsApp]\n\n─────────────────────────────────────\nPRESTATIONS\n─────────────────────────────────────\nSite vitrine 5 pages (Home, À propos, Services,\nPortfolio, Contact)                           150 000 FCFA HT\n- Design UI personnalisé (charte graphique fournie)\n- Responsive mobile + tablette\n- Formulaire de contact + intégration WhatsApp\n- Optimisation SEO on-page\n- Hébergement + nom de domaine 1 an inclus\n\nMaintenance annuelle (optionnelle)             36 000 FCFA HT\n- Mises à jour contenu (2h/mois)\n- Sauvegardes hebdomadaires\n- Support WhatsApp J+7\n\n─────────────────────────────────────\nTOTAL HT                                      150 000 FCFA\nTVA 19,25 %                                    28 875 FCFA\nTOTAL TTC                                     178 875 FCFA\n─────────────────────────────────────\n\nCONDITIONS DE PAIEMENT\n• Acompte 50 % à la commande : 89 438 FCFA\n• Solde 50 % à la livraison : 89 437 FCFA\n• Moyens : MTN MoMo / Orange Money / Virement\n\nDÉLAI DE LIVRAISON : 14 jours ouvrés après réception de l'acompte\n\nSignature client : _______________\nDate : _______________"}, {'type': 'email_accompagnement', 'title': "Email d'accompagnement du devis", 'content': 'Objet : Votre devis KNB — Site vitrine [NOM CLIENT]\n\nBonjour [Prénom],\n\nSuite à notre échange, vous trouverez ci-joint votre devis pour la création de votre site vitrine.\n\nEn résumé : site 5 pages, responsive, avec formulaire WhatsApp intégré — livrable en 2 semaines après acompte.\n\nJe reste disponible pour en discuter : WhatsApp [NUMÉRO] ou répondez directement à cet email.\n\nCordialement,\n[Votre prénom]\nKNB — Votre vision. Notre code.\nYaoundé | [NUMÉRO]'}],
            "followups": ['Le client a-t-il mentionné un budget ou une contrainte de délai ?', 'Faut-il inclure une option de maintenance dans la proposition ?', "Y a-t-il des concurrents identifiés sur ce devis ? (permet d'anticiper la comparaison)"],
            "score": 0.78,
        }
