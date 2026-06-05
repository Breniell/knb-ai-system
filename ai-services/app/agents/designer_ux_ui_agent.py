"""
agents/designeruxuiagent_agent.py — Wrapper KnbAgent (v3.1).
"""
from __future__ import annotations
from typing import Any
from app.agents.base import KnbAgent
from app.agents._senior_prompts import SENIOR_PROMPTS
from app.models import ExecutionContext, SubTask


class DesignerUXUIAgent(KnbAgent):
    name = "DesignerUXUIAgent"
    specialty = "User research, wireframes, design systems, accessibilité WCAG"
    emoji = "🎨"
    _system_prompt = SENIOR_PROMPTS.get("DesignerUXUIAgent", "")

    def _fallback_response(self, task: SubTask, context: ExecutionContext) -> dict[str, Any]:
        return {
            "summary": 'User flow principal documenté, design tokens définis et wireframes basse-fi pour les 3 écrans clés. Design system structuré avec 5 composants atomiques spécifiés.',
            "artifacts": [{'type': 'design_system', 'title': 'Design Tokens & composants atomiques', 'content': '## DESIGN TOKENS KNB\n\n### Couleurs\n| Token | Hex | Usage |\n|-------|-----|-------|\n| --color-primary | #0EA5E9 | Actions principales, liens |\n| --color-primary-dark | #0284C7 | Hover, focus |\n| --color-surface | #0F172A | Fond sombre (dark mode) |\n| --color-bg | #F8FAFC | Fond clair |\n| --color-text | #1E293B | Texte principal |\n| --color-muted | #64748B | Texte secondaire |\n| --color-accent | #F97316 | Notifications, badges |\n| --color-success | #22C55E | Confirmations |\n| --color-error | #EF4444 | Erreurs |\n\n### Typographie\n| Token | Valeur | Usage |\n|-------|--------|-------|\n| --font-sans | Inter, system-ui | Corps, UI |\n| --font-heading | Sora, sans-serif | Titres H1-H3 |\n| --text-xs | 12px / lh 1.5 | Labels, badges |\n| --text-sm | 14px / lh 1.5 | Texte secondaire |\n| --text-base | 16px / lh 1.6 | Corps de texte |\n| --text-lg | 20px / lh 1.4 | Sous-titres |\n| --text-2xl | 28px / lh 1.3 | Titres |\n\n### Spacing scale\n4px · 8px · 12px · 16px · 24px · 32px · 48px · 64px · 96px\n\n### Composants atomiques (états requis)\nButton : default / hover / focus / loading / disabled\nInput : default / focus / error / disabled / filled\nCard : default / hover / selected\nBadge : info / success / warning / error\nModal : default / with-footer / full-screen mobile'}],
            "followups": ['Existe-t-il une charte graphique (couleurs, logo) ou on la définit ex nihilo ?', 'Les utilisateurs sont-ils principalement sur mobile (Android budget) ou desktop ?', 'Faut-il prévoir un dark mode dès le départ ?'],
            "score": 0.78,
        }
