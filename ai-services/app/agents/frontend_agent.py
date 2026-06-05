"""
agents/frontend_agent.py — Agent frontend "généraliste" (workflow-level).

NB : pour le travail concret sur React/Next.js, c'est DevFrontendAgent qui est
appelé. FrontendAgent est conservé pour rétro-compatibilité avec le workflow
historique. Refactoré pour hériter de KnbAgent et émettre un schéma cohérent
(artifacts = list[dict]) — l'ancien retournait un dict, ce qui faisait crasher
Pydantic à chaque exécution.
"""

from __future__ import annotations

from typing import Any

from app.agents.base import KnbAgent
from app.agents.knb_context import KNB_CONTEXT
from app.models import ExecutionContext, SubTask


class FrontendAgent(KnbAgent):
    name = "FrontendAgent"
    specialty = "Architecture frontend, design tokens, optimisation UI"
    emoji = "🖼️"

    _system_prompt = f"""
{KNB_CONTEXT}

Tu es un Architecte Frontend Senior. Tu produis des recommandations
stratégiques (pas du code brut — c'est le rôle de DevFrontendAgent).

Tu livres :
- la stratégie de composants (architecture, design tokens, librairies)
- les contraintes : accessibilité WCAG AA, performance Core Web Vitals,
  responsive mobile-first
- la stratégie de state/data (React Query, Zustand)
- les optimisations (lazy loading, code splitting, image optimization)

Format JSON OBLIGATOIRE :
{{
  "summary": "résumé exécutif 2-4 phrases",
  "artifacts": [
    {{"type": "strategy", "title": "...", "content": "..."}},
    {{"type": "design_tokens", "title": "...", "content": "..."}}
  ],
  "followups": ["..."],
  "score": 0.0-1.0
}}
""".strip()

    def _fallback_response(self, task: SubTask, context: ExecutionContext) -> dict[str, Any]:
        return {
            "summary": (
                f"Stratégie frontend pour : {task.title}. Architecture en "
                "composants atomiques, React Query pour le data fetching, "
                "Tailwind + design tokens KNB pour le visuel."
            ),
            "artifacts": [
                {
                    "type": "strategy",
                    "title": "Stratégie composants frontend",
                    "content": (
                        "ARCHITECTURE COMPOSANTS (Atomic Design)\n"
                        "- Atoms : Button, Input, Label, Icon, Badge\n"
                        "- Molecules : FormField, Card, NavItem, Modal\n"
                        "- Organisms : Header, Footer, ProjectCard, Sidebar\n"
                        "- Templates : DashboardLayout, AuthLayout, PublicLayout\n"
                        "- Pages : composées via Next.js App Router\n\n"
                        "STATE MANAGEMENT\n"
                        "- Server state : React Query (stale-while-revalidate)\n"
                        "- Client state global : Zustand (léger, sans boilerplate)\n"
                        "- État de formulaire : React Hook Form + Zod\n\n"
                        "PERFORMANCE\n"
                        "- Next.js Image pour toutes les images\n"
                        "- dynamic() pour les composants lourds (charts, éditeurs)\n"
                        "- Cache HTTP via cache-control headers"
                    ),
                },
                {
                    "type": "design_tokens",
                    "title": "Design tokens KNB",
                    "content": (
                        "// design-tokens.ts\n"
                        "export const tokens = {\n"
                        "  color: {\n"
                        "    primary: '#0EA5E9',\n"
                        "    dark: '#060A14',\n"
                        "    accent: '#F97316',\n"
                        "    surface: '#0F172A',\n"
                        "  },\n"
                        "  font: { sans: 'Inter, system-ui', mono: 'JetBrains Mono' },\n"
                        "  radius: { sm: '4px', md: '8px', lg: '12px' },\n"
                        "  spacing: { xs: 4, sm: 8, md: 16, lg: 24, xl: 32 },\n"
                        "};\n"
                    ),
                },
            ],
            "followups": [
                "Quelle est la cible principale (mobile / desktop / les deux) ?",
                "Y a-t-il un design system existant à respecter ?",
                "Quel CMS / source de contenu : Sanity, Strapi, Firestore ?",
            ],
            "score": 0.78,
        }
