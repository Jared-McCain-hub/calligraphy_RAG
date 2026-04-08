from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health", summary="健康检查")
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "calligraphy-rag-backend",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
