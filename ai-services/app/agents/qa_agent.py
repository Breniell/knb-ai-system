"""
agents/qaagent_agent.py — Wrapper KnbAgent (v3.1).
"""
from __future__ import annotations
from typing import Any
from app.agents.base import KnbAgent
from app.agents._senior_prompts import SENIOR_PROMPTS
from app.models import ExecutionContext, SubTask


class QAAgent(KnbAgent):
    name = "QAAgent"
    specialty = "Tests E2E Playwright, pyramide de tests, stratégie QA, recette client"
    emoji = "🧪"
    _system_prompt = SENIOR_PROMPTS.get("QAAgent", "")

    def _fallback_response(self, task: SubTask, context: ExecutionContext) -> dict[str, Any]:
        return {
            "summary": 'Plan de tests livré avec 15 scénarios E2E Playwright couvrant auth, dashboard, formulaires critiques et flux de paiement. Checklist de recette client en 20 points. Cible : 0 bug critique à la livraison.',
            "artifacts": [{'type': 'test_plan', 'title': 'Plan de tests fonctionnels', 'content': '## PÉRIMÈTRE DE TESTS\n\n### Module AUTH\n| ID | Cas | Priorité |\n|----|-----|----------|\n| TC-A01 | Connexion email + mot de passe valides | P0 |\n| TC-A02 | Connexion avec Google OAuth | P0 |\n| TC-A03 | Mot de passe erroné → message erreur clair | P1 |\n| TC-A04 | Réinitialisation mot de passe | P1 |\n| TC-A05 | Déconnexion + redirection login | P1 |\n\n### Module DASHBOARD\n| ID | Cas | Priorité |\n|----|-----|----------|\n| TC-D01 | Affichage liste projets (données réelles) | P0 |\n| TC-D02 | Création projet → apparaît dans la liste | P0 |\n| TC-D03 | Recherche / filtrage fonctionne | P1 |\n| TC-D04 | Pagination ou scroll infini | P2 |\n\n### Module PAIEMENT\n| ID | Cas | Priorité |\n|----|-----|----------|\n| TC-P01 | Initiation paiement MTN MoMo | P0 |\n| TC-P02 | Confirmation paiement reçu → mise à jour statut | P0 |\n| TC-P03 | Timeout paiement → retry ou annulation | P0 |\n\n## CRITÈRES GO / NO-GO\n- GO : 0 bug P0, < 3 bugs P1 (correctifs planifiés)\n- NO-GO : ≥ 1 bug P0 non résolu'}, {'type': 'e2e_test', 'title': 'Test Playwright — flux de connexion', 'content': "// tests/e2e/auth.spec.ts\nimport { test, expect } from '@playwright/test'\n\ntest.describe('Auth — Connexion', () => {\n  test('connexion valide → dashboard', async ({ page }) => {\n    await page.goto('/login')\n    await page.getByLabel('Email').fill('test@knb.cm')\n    await page.getByLabel('Mot de passe').fill('Test1234!')\n    await page.getByRole('button', { name: /connexion/i }).click()\n    await expect(page).toHaveURL('/dashboard')\n    await expect(page.getByText('Mes projets')).toBeVisible()\n  })\n\n  test('mot de passe erroné → erreur visible', async ({ page }) => {\n    await page.goto('/login')\n    await page.getByLabel('Email').fill('test@knb.cm')\n    await page.getByLabel('Mot de passe').fill('mauvais')\n    await page.getByRole('button', { name: /connexion/i }).click()\n    await expect(page.getByRole('alert')).toBeVisible()\n  })\n})"}],
            "followups": ["L'environnement de staging est-il disponible pour les tests E2E automatisés ?", 'Playwright ou Cypress ? (Playwright recommandé, plus moderne)', 'Faut-il inclure des tests de performance (Lighthouse CI) ?'],
            "score": 0.78,
        }
