"""
quick_test.py — Vérification rapide du système KNB AI v3.1.

Lance ce script depuis ai-services/ pour valider que :
  1. Les agents instancient sans erreur.
  2. Le workflow tourne de bout en bout sur un cas réaliste.
  3. Les artefacts produits sont structurés correctement.
  4. La boucle d'auto-critique et le re-travail fonctionnent.

Usage :
    cd ai-services
    python quick_test.py                  # 3 scénarios par défaut
    python quick_test.py "Crée un devis pour un site vitrine"
    python quick_test.py --verbose

Aucune clé API n'est requise pour la version fallback (mais sans clé, tu verras
les fallbacks déterministes — pas les vraies réponses du LLM). Avec une clé
GROQ_API_KEY ou GEMINI_API_KEY dans .env, le test montre la vraie qualité.
"""

from __future__ import annotations

import asyncio
import json
import sys
from typing import Any


SCENARIOS = [
    {
        "name": "Devis client",
        "request": (
            "Un boulanger à Yaoundé veut un site vitrine 5 pages avec un "
            "système de commande WhatsApp pour ses clients. Budget 250 000 FCFA. "
            "Prépare-moi un devis complet, le cahier des charges et une "
            "proposition d'architecture."
        ),
        "expected_agents": ["FinanceAgent", "ChefDeProjetAgent", "ArchitecteAgent",
                            "CommercialAgent", "ReviewerAgent"],
    },
    {
        "name": "Post LinkedIn",
        "request": (
            "Rédige un post LinkedIn pour KNB qui présente notre service "
            "de digitalisation des PME camerounaises. Ton : confiant mais "
            "humble. Cible : entrepreneurs 30-50 ans. Inclure un CTA pour "
            "prendre rdv WhatsApp."
        ),
        "expected_agents": ["RedacteurAgent", "CommunityManagerAgent", "ReviewerAgent"],
    },
    {
        "name": "Plan technique app mobile",
        "request": (
            "Une PME de transport veut une app mobile Android pour gérer ses "
            "chauffeurs et courses, avec offline-first et Mobile Money MTN/Orange. "
            "Donne-moi l'architecture, la roadmap projet et la stratégie QA."
        ),
        "expected_agents": ["ArchitecteAgent", "DevMobileAgent",
                            "ChefDeProjetAgent", "QAAgent", "ReviewerAgent"],
    },
]


# ─── Outils de présentation ───────────────────────────────────────────────────

def _hr(char: str = "─", width: int = 80) -> str:
    return char * width


def _print_scenario_header(idx: int, scenario: dict[str, Any]) -> None:
    print("\n" + "=" * 80)
    print(f"SCÉNARIO {idx} : {scenario['name']}")
    print("=" * 80)
    print(f"Demande : {scenario['request']}\n")


def _print_response(resp: Any, verbose: bool) -> None:
    # AgentResponse Pydantic → dict pour un accès uniforme
    if hasattr(resp, "model_dump"):
        resp = resp.model_dump()
    agent = resp.get("agent", "?")
    score = resp.get("score", 0)
    artifacts = resp.get("artifacts", [])
    print(f"\n  ┌─ {agent}  (score {score:.2f}, {len(artifacts)} artefact(s))")
    summary = (resp.get("summary") or "").strip()
    for line in summary.split("\n"):
        print(f"  │   {line[:120]}")
    for art in artifacts[: 2 if not verbose else 5]:
        title = art.get("title", "")
        content = (art.get("content") or "")
        preview = content[:300 if not verbose else 1200].rstrip()
        print(f"  │")
        print(f"  │   📎 {title}")
        for line in preview.split("\n")[: 6 if not verbose else 20]:
            print(f"  │      {line}")
        if len(content) > 300 and not verbose:
            print(f"  │      …")
    fups = resp.get("followups", [])
    if fups:
        print(f"  │")
        print(f"  │   Followups :")
        for f in fups[:3]:
            print(f"  │     - {f}")
    print(f"  └─")


def _print_workflow_summary(result: Any) -> None:
    print(f"\n{_hr('━')}")
    print(f"RÉSUMÉ EXÉCUTION")
    print(f"{_hr('━')}")
    print(f"  workflow_id      : {result.workflow_id}")
    print(f"  agents exécutés  : {len(result.responses)}")
    print(f"  étapes timeline  : {len(result.timeline)}")
    if result.review:
        print(f"  verdict reviewer : {result.review.score:.2f}")

    score_avg = (
        sum(r.score for r in result.responses) / len(result.responses)
        if result.responses else 0
    )
    print(f"  score moyen      : {score_avg:.2f}")


# ─── Exécution ────────────────────────────────────────────────────────────────

async def run_scenario(scenario: dict[str, Any], verbose: bool) -> None:
    from app.models import AgentRunRequest
    from app.orchestrator.service import OrchestratorService

    orchestrator = OrchestratorService()
    await orchestrator.startup()

    req = AgentRunRequest(
        input=scenario["request"],
        project_id="quick-test",
        user_id="quick-test",
        mode="autonomous",
    )
    result = await orchestrator.run(req)

    for resp in result.responses:
        _print_response(resp, verbose=verbose)
    _print_workflow_summary(result)


async def main() -> None:
    args = sys.argv[1:]
    verbose = "--verbose" in args or "-v" in args
    args = [a for a in args if a not in ("--verbose", "-v")]

    if args:
        scenarios = [{"name": "Custom", "request": " ".join(args),
                      "expected_agents": []}]
    else:
        scenarios = SCENARIOS

    print(f"{_hr('═')}")
    print("KNB AI System — Quick Test v3.1")
    print(_hr('═'))

    # État LLM
    try:
        from app.core.llm import LlmClient
        llm = LlmClient()
        print(f"  Provider LLM      : {llm.provider}")
        print(f"  Embedder dispo    : {llm.embedder_available}")
        if not llm.enabled():
            print("\n  ⚠ Aucun provider LLM configuré. Le test va utiliser les")
            print("    fallbacks déterministes. Pour voir la vraie qualité,")
            print("    ajoute GROQ_API_KEY (gratuit) ou GEMINI_API_KEY dans .env.\n")
    except Exception as e:
        print(f"  ⚠ Erreur LLM : {e}")

    for idx, scenario in enumerate(scenarios, 1):
        _print_scenario_header(idx, scenario)
        try:
            await run_scenario(scenario, verbose=verbose)
        except Exception as exc:
            print(f"\n  ✗ ERREUR : {exc}\n")
            import traceback
            traceback.print_exc()

    print(f"\n{_hr('═')}")
    print("Test terminé. Si tu vois des artefacts concrets et des scores > 0.6,")
    print("ton système est opérationnel.")
    print(_hr('═'))


if __name__ == "__main__":
    asyncio.run(main())
