from fastapi import APIRouter, Depends, Query

from app.orchestrator.dependencies import get_orchestrator
from app.orchestrator.service import OrchestratorService

router = APIRouter()


@router.get("/memory/search")
async def search_memory(
    query: str = Query(..., min_length=1),
    limit: int = Query(default=5, ge=1, le=20),
    project_id: str | None = Query(default=None),
    orchestrator: OrchestratorService = Depends(get_orchestrator),
):
    return {
        "ok": True,
        "results": orchestrator.vector.search(query=query, limit=limit, project_id=project_id),
    }

