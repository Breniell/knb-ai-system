from fastapi import APIRouter, Depends

from app.core.metrics import metrics
from app.orchestrator.dependencies import get_orchestrator
from app.orchestrator.service import OrchestratorService

router = APIRouter()


@router.get("/monitoring/metrics")
async def get_metrics():
    return {"ok": True, "metrics": metrics.snapshot()}


@router.get("/monitoring/workflows/{workflow_id}")
async def workflow_state(
    workflow_id: str, orchestrator: OrchestratorService = Depends(get_orchestrator)
):
    state = await orchestrator.redis.get_short_term(f"workflow:{workflow_id}")
    return {"ok": True, "workflow_id": workflow_id, "state": state}

