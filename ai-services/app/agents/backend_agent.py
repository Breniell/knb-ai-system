"""
agents/backend_agent.py — Agent backend "généraliste" (workflow-level).

Pour le travail concret sur APIs/Prisma/PostgreSQL, c'est DevBackendAgent qui
est appelé. BackendAgent existe pour rétro-compatibilité workflow. Refactoré
pour hériter de KnbAgent et émettre des artifacts list[dict] (vs dict avant,
ce qui faisait crasher Pydantic).
"""

from __future__ import annotations

from typing import Any

from app.agents.base import KnbAgent
from app.agents.knb_context import KNB_CONTEXT
from app.models import ExecutionContext, SubTask


class BackendAgent(KnbAgent):
    name = "BackendAgent"
    specialty = "Architecture backend, modélisation données, contrats API"
    emoji = "🛠️"

    _system_prompt = f"""
{KNB_CONTEXT}

Tu es un Architecte Backend Senior. Tu fournis des plans d'architecture,
des modèles de données et des contrats d'API (le code détaillé est produit
par DevBackendAgent).

Tu livres :
- la liste des endpoints REST/GraphQL nécessaires (verbe + chemin + résumé)
- le modèle de données (entités, relations, index recommandés)
- la stratégie d'auth (Firebase Auth, JWT, RBAC si besoin)
- les optimisations critiques : indexes, idempotency, rate-limit, caching

Format JSON OBLIGATOIRE :
{{
  "summary": "résumé 2-4 phrases, valeur livrée",
  "artifacts": [
    {{"type": "api_contract", "title": "...", "content": "..."}},
    {{"type": "data_model", "title": "...", "content": "..."}}
  ],
  "followups": ["..."],
  "score": 0.0-1.0
}}
""".strip()

    def _fallback_response(self, task: SubTask, context: ExecutionContext) -> dict[str, Any]:
        return {
            "summary": (
                f"Plan backend pour : {task.title}. Modèle relationnel "
                "PostgreSQL/Prisma, API REST versionnée, Firebase Auth, "
                "idempotency keys sur tous les POST critiques."
            ),
            "artifacts": [
                {
                    "type": "api_contract",
                    "title": "Contrats d'API REST",
                    "content": (
                        "AUTHENTIFICATION\n"
                        "POST   /api/auth/firebase   → échange token Firebase contre session\n"
                        "POST   /api/auth/logout     → invalidation session\n\n"
                        "PROJETS\n"
                        "GET    /api/projects        → liste paginée (cursor)\n"
                        "POST   /api/projects        → création (Idempotency-Key requis)\n"
                        "GET    /api/projects/:id    → détail + relations\n"
                        "PATCH  /api/projects/:id    → mise à jour partielle\n"
                        "DELETE /api/projects/:id    → suppression logique\n\n"
                        "TÂCHES\n"
                        "GET    /api/projects/:id/tasks\n"
                        "POST   /api/projects/:id/tasks\n"
                        "PATCH  /api/tasks/:id\n\n"
                        "WORKFLOWS IA\n"
                        "POST   /api/ai/run          → lance un workflow d'agents\n"
                        "GET    /api/ai/workflows/:id  → état + timeline"
                    ),
                },
                {
                    "type": "data_model",
                    "title": "Modèle de données (Prisma)",
                    "content": (
                        "model User {\n"
                        "  id        String   @id @default(cuid())\n"
                        "  email     String   @unique\n"
                        "  name      String?\n"
                        "  projects  Project[]\n"
                        "  createdAt DateTime @default(now())\n"
                        "}\n\n"
                        "model Project {\n"
                        "  id          String   @id @default(cuid())\n"
                        "  name        String\n"
                        "  status      ProjectStatus @default(ACTIVE)\n"
                        "  ownerId     String\n"
                        "  owner       User     @relation(fields:[ownerId], references:[id])\n"
                        "  tasks       Task[]\n"
                        "  workflows   WorkflowRun[]\n"
                        "  createdAt   DateTime @default(now())\n"
                        "  @@index([ownerId, status])\n"
                        "}\n\n"
                        "enum ProjectStatus { ACTIVE PAUSED COMPLETED CANCELLED }"
                    ),
                },
            ],
            "followups": [
                "Combien d'utilisateurs simultanés est-il prévu ?",
                "Avez-vous besoin de la pagination cursor ou offset ?",
                "Quels webhooks externes (paiement, email) faut-il intégrer ?",
            ],
            "score": 0.82,
        }
