from fastapi import APIRouter, Query, BackgroundTasks
from pydantic import BaseModel

from app.tools.learning_engine import (
    get_cached_knowledge,
    get_top_knowledge,
    invalidate_cache,
    learn_from_web,
    search_knowledge,
)

router = APIRouter()


# ── Endpoints originaux (inchangés) ──────────────────────────────────────────

@router.get("/learning/knowledge")
async def get_knowledge(topic: str = Query(..., description="Topic to search")):
    results = search_knowledge(topic)
    cached = get_cached_knowledge(topic)
    return {"ok": True, "topic": topic, "cached_insights": cached, "search_results": results}


@router.get("/learning/top")
async def top_knowledge(limit: int = Query(10, ge=1, le=50)):
    items = get_top_knowledge(limit=limit)
    return {"ok": True, "count": len(items), "items": items}


@router.post("/learning/trigger")
async def trigger_learning(body: dict):
    topic = str(body.get("topic", "")).strip()
    context_hint = str(body.get("context_hint", ""))
    if not topic:
        return {"ok": False, "error": "topic is required"}
    insights = await learn_from_web(topic, context_hint)
    return {"ok": True, "topic": topic, "insights": insights, "count": len(insights)}


@router.delete("/learning/cache")
async def delete_cache(topic: str = Query(..., description="Topic cache to invalidate")):
    deleted = invalidate_cache(topic)
    return {"ok": True, "topic": topic, "deleted": deleted}


# ── Nouveau : retrain complet via scheduler ───────────────────────────────────

class RetrainRequest(BaseModel):
    force: bool = False
    agent_name: str | None = None


@router.post("/learning/retrain")
async def retrain(req: RetrainRequest, background_tasks: BackgroundTasks):
    """
    Déclenche un cycle d'apprentissage autonome sur les curricula des agents.
    - force=false : ne reforme que les agents dont les sujets sont obsolètes
    - force=true  : reforme tout, même les sujets récents
    - agent_name  : limite à un seul agent (optionnel)

    L'opération s'exécute en arrière-plan.
    Consulte /healthz pour voir la progression (scheduler.last_cycle).
    """
    try:
        from app.tools.scheduler import scheduler
        background_tasks.add_task(
            scheduler.trigger_now,
            agent_name=req.agent_name,
            force=req.force,
        )
        return {
            "ok": True,
            "message": "Cycle d'apprentissage lancé en arrière-plan.",
            "force": req.force,
            "agent_filter": req.agent_name,
            "monitor": "GET /healthz pour voir scheduler.last_cycle",
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.get("/learning/status")
async def learning_status():
    """Retourne l'état du scheduler et les statistiques d'apprentissage."""
    try:
        from app.tools.scheduler import scheduler
        return {
            "ok": True,
            "scheduler": scheduler.status(),
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.get("/learning/curricula")
async def list_curricula():
    """Liste tous les curricula disponibles par agent avec leurs sources."""
    try:
        from app.tools.learning_resources import ALL_CURRICULA, get_free_certifications
        result = {}
        for name, curriculum in ALL_CURRICULA.items():
            result[name] = {
                "topics": [
                    {"topic": r.topic, "urls": r.urls, "freshness_hours": r.freshness_hours}
                    for r in curriculum.resources
                ],
                "certifications": curriculum.certifications,
            }
        free_certs = get_free_certifications()
        return {"ok": True, "agents": result, "free_certifications": free_certs}
    except Exception as e:
        return {"ok": False, "error": str(e)}
