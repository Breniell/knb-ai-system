from app.orchestrator.service import OrchestratorService, orchestrator_service


def get_orchestrator() -> OrchestratorService:
    return orchestrator_service
