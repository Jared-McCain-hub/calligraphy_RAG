from app.api.v1.admin_ingest import router as admin_router
from app.api.v1.calligraphers import router as calligraphers_router
from app.api.v1.chat import router as chat_router
from app.api.v1.graph import router as graph_router
from app.api.v1.health import router as health_router
from app.api.v1.search import router as search_router
from app.api.v1.works import router as works_router

__all__ = [
    "admin_router",
    "calligraphers_router",
    "chat_router",
    "graph_router",
    "health_router",
    "search_router",
    "works_router",
]
