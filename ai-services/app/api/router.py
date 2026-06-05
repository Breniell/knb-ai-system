from fastapi import APIRouter

from .routes.agents import router as agents_router
from .routes.health import router as health_router
from .routes.learning import router as learning_router
from .routes.memory import router as memory_router
from .routes.monitoring import router as monitoring_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(agents_router)
api_router.include_router(memory_router)
api_router.include_router(monitoring_router)
api_router.include_router(learning_router)

# Alias for compatibility
router = api_router
