"""
agents/devopsagent_agent.py — Wrapper KnbAgent (v3.1).
"""
from __future__ import annotations
from typing import Any
from app.agents.base import KnbAgent
from app.agents._senior_prompts import SENIOR_PROMPTS
from app.models import ExecutionContext, SubTask


class DevOpsAgent(KnbAgent):
    name = "DevOpsAgent"
    specialty = "GitHub Actions, Docker, Vercel, Railway, monitoring, CI/CD"
    emoji = "⚙️"
    _system_prompt = SENIOR_PROMPTS.get("DevOpsAgent", "")

    def _fallback_response(self, task: SubTask, context: ExecutionContext) -> dict[str, Any]:
        return {
            "summary": 'Pipeline CI/CD complet livré : lint → tests → build → deploy automatique sur Vercel (front) et Railway (API). Dockerfile optimisé multi-stage, coût infra 6 500 FCFA/mois pour le setup recommandé.',
            "artifacts": [{'type': 'github_actions', 'title': 'Pipeline GitHub Actions CI/CD', 'content': "# .github/workflows/deploy.yml\nname: CI/CD Pipeline\n\non:\n  push:\n    branches: [main, develop]\n  pull_request:\n    branches: [main]\n\njobs:\n  test:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n      - uses: actions/setup-node@v4\n        with: { node-version: '20', cache: 'npm' }\n      - run: npm ci\n      - run: npm run lint\n      - run: npm run typecheck\n      - run: npm run test -- --coverage\n      - run: npm run build\n\n  deploy-production:\n    needs: test\n    if: github.ref == 'refs/heads/main'\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n      - name: Deploy to Vercel\n        uses: amondnet/vercel-action@v25\n        with:\n          vercel-token: ${{ secrets.VERCEL_TOKEN }}\n          vercel-args: '--prod'\n          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}\n          vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}\n      - name: Deploy API to Railway\n        env:\n          RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}\n        run: npx railway up --service api"}],
            "followups": ['Environnements nécessaires : dev / staging / prod ou seulement dev/prod ?', 'Un Dockerfile existe déjà ou on part de zéro ?', 'Besoin de notifications Slack/WhatsApp sur les déploiements ?'],
            "score": 0.78,
        }
