"""
app/main.py — Bootstrap FastAPI KNB AI System.

Changements vs version originale :
  - Branchement du TrainingScheduler (auto-formation en boucle, pas seulement
    une fois au démarrage).
  - Arrêt propre du scheduler au shutdown.
  - Healthz enrichi : provider LLM actif + statut scheduler + métriques.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import router
from app.core.logging import get_logger

logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ═══════════ DÉMARRAGE ═══════════════════════════════════════════════════
    logger.info("=============================================")
    logger.info("  KNB AI System v3.1 — Démarrage")
    logger.info("  Agence digitale IA — Yaoundé, Cameroun")
    logger.info("=============================================")

    # Firebase
    try:
        from app.core.firebase import get_firestore_client
        db = get_firestore_client()
        if db:
            logger.info("[OK] Firebase Firestore connecté")
        else:
            logger.warning("[--] Firebase désactivé — mode sans persistance")
    except Exception as e:
        logger.warning("[!!] Firebase erreur : %s", e)

    # LLM
    llm_provider = "fallback"
    try:
        from app.core.llm import LlmClient
        llm = LlmClient()
        llm_provider = llm.provider
        embedder = "Gemini text-embedding-004" if llm.embedder_available else "désactivé"
        logger.info("[OK] LLM provider : %s | Embedder : %s", llm_provider, embedder)
    except Exception as e:
        logger.warning("[!!] LLM erreur : %s", e)

    # Orchestrateur
    try:
        from app.orchestrator.service import orchestrator_service
        await orchestrator_service.startup()
        logger.info("[OK] Orchestrateur démarré")
    except Exception as e:
        logger.warning("[!!] Orchestrateur démarrage partiel : %s", e)

    # Scheduler d'auto-formation (tourne en boucle)
    try:
        from app.tools.scheduler import scheduler
        await scheduler.start()
        logger.info("[OK] Scheduler d'auto-formation lancé")
    except Exception as e:
        logger.warning("[!!] Scheduler erreur : %s", e)

    logger.info("[OK] KNB AI System prêt — http://localhost:8000")
    logger.info("     Agents : 18 | Docs : /docs | Healthz : /healthz")

    yield  # ← L'application tourne ici

    # ═══════════ ARRÊT ═══════════════════════════════════════════════════════
    try:
        from app.tools.scheduler import scheduler
        await scheduler.stop()
    except Exception as e:
        logger.warning("Scheduler.stop erreur : %s", e)
    logger.info("KNB AI System arrêté proprement")


app = FastAPI(
    title="KNB AI System",
    description="Agence IA complète — KNB, Yaoundé, Cameroun",
    version="3.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3001",
        "http://localhost:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")


@app.api_route("/healthz", methods=["GET", "HEAD"])
async def health():
    """Healthcheck enrichi avec état des composants critiques."""
    try:
        from app.core.llm import LlmClient
        from app.tools.scheduler import scheduler
        llm = LlmClient()
        return {
            "ok": True,
            "service": "knb-ai-system",
            "version": "3.1.0",
            "llm": {
                "provider": llm.provider,
                "embedder": llm.embedder_available,
                "metrics": {
                    "calls": llm.metrics.calls,
                    "json_failures": llm.metrics.json_failures,
                    "embed_calls": llm.metrics.embed_calls,
                },
            },
            "scheduler": {
                "running": scheduler.running,
                "last_cycle": scheduler.last_cycle_summary,
            },
        }
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}
