from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import (
    admin_router,
    calligraphers_router,
    chat_router,
    graph_router,
    health_router,
    search_router,
    works_router,
)
from app.api.v1.qdrant_chat import router as qdrant_router


api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(chat_router)
api_router.include_router(qdrant_router)
api_router.include_router(search_router)
api_router.include_router(graph_router)
api_router.include_router(works_router)
api_router.include_router(calligraphers_router)
api_router.include_router(admin_router)
