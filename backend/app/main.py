from __future__ import annotations

from fastapi import FastAPI

from app.api import api_router
from app.core.config import settings
from app.core.security import APIKeyAuthMiddleware, IPRateLimitMiddleware, configure_logging


def create_app() -> FastAPI:
    configure_logging()
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
        description="中国书法跨语言问答系统 MVP 后端接口。",
    )
    app.add_middleware(IPRateLimitMiddleware)
    app.add_middleware(APIKeyAuthMiddleware)
    app.include_router(api_router, prefix=settings.api_prefix)
    return app


app = create_app()
