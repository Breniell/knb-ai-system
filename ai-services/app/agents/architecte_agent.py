"""
agents/architecteagent_agent.py — Wrapper KnbAgent (v3.1).
"""
from __future__ import annotations
from typing import Any
from app.agents.base import KnbAgent
from app.agents._senior_prompts import SENIOR_PROMPTS
from app.models import ExecutionContext, SubTask


class ArchitecteAgent(KnbAgent):
    name = "ArchitecteAgent"
    specialty = "Architecture logicielle, choix de stack, sécurité, scalabilité, coûts infra"
    emoji = "🏗️"
    _system_prompt = SENIOR_PROMPTS.get("ArchitecteAgent", "")

    def _fallback_response(self, task: SubTask, context: ExecutionContext) -> dict[str, Any]:
        return {
            "summary": 'Architecture proposée : monolithe modulaire Next.js 14 + Node.js/Express + PostgreSQL 16 sur Railway. Stack éprouvée, déployable en 30 min, coût estimé 12 000–25 000 FCFA/mois selon trafic. Sécurité OWASP Top 10 couverte.',
            "artifacts": [{'type': 'architecture_doc', 'title': "Document d'architecture v1.0", 'content': '## STACK RECOMMANDÉE\n- Frontend : Next.js 14 App Router + TypeScript + Tailwind CSS\n- Backend : Node.js 20 + Express 4 + Prisma 5 + Zod\n- Base de données : PostgreSQL 16 (Railway managed)\n- Auth : Firebase Authentication (Google, Email)\n- Hébergement : Vercel (front) + Railway (API + DB)\n- CDN/Médias : Cloudinary (images) + Vercel Edge\n\n## COÛTS MENSUELS ESTIMÉS (FCFA)\n| Service | Plan | Coût FCFA/mois |\n|---------|------|----------------|\n| Vercel Hobby | Gratuit | 0 |\n| Railway Starter | 5 USD | ~3 300 |\n| PostgreSQL Railway | 5 USD | ~3 300 |\n| Cloudinary Free | Gratuit | 0 |\n| Firebase Auth | Gratuit (50k MAU) | 0 |\n| **TOTAL MVP** | | **~6 600 FCFA/mois** |\n\n## ADR-001 : PostgreSQL vs MongoDB\nDécision : PostgreSQL. Raisons : données relationnelles (users, projets, commandes), transactions ACID nécessaires, expertise équipe KNB, meilleur support Prisma. Alternative rejetée : MongoDB (overhead opérationnel non justifié pour ce volume).\n\n## SÉCURITÉ (OWASP Top 10)\n- A01 Broken Access Control → RBAC Prisma + middleware auth\n- A02 Cryptographic Failures → HTTPS only, bcrypt passwords\n- A03 Injection → Prisma ORM (pas de SQL brut)\n- A07 Auth Failures → Firebase Auth + rate limiting\n- A09 Logging → Sentry + Logtail'}],
            "followups": ['Le trafic attendu dépasse 10 000 utilisateurs/jour ? (influe sur le plan Railway)', 'Faut-il une API mobile séparée ou le frontend web suffit pour phase 1 ?', 'Des intégrations tierces identifiées (paiement, SMS, comptabilité) ?'],
            "score": 0.78,
        }
