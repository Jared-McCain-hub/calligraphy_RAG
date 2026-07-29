from __future__ import annotations

import logging
import time
from collections import defaultdict, deque
from threading import Lock

from fastapi import status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.config import settings

logger = logging.getLogger("app.security")


def configure_logging() -> None:
    if logging.getLogger().handlers:
        return
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def _get_client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for", "")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    if request.client is None:
        return "unknown"
    return request.client.host


def _is_exempt(path: str, exempt_paths: tuple[str, ...]) -> bool:
    return any(path == exempt or path.startswith(f"{exempt}/") for exempt in exempt_paths)


class APIKeyAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        if not settings.api_auth_enabled or _is_exempt(request.url.path, settings.api_auth_exempt_paths):
            return await call_next(request)

        expected_key = settings.api_auth_key
        provided_key = request.headers.get(settings.api_auth_header_name)
        client_ip = _get_client_ip(request)

        if not expected_key:
            logger.error("API auth enabled but API_AUTH_KEY is empty.")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "Server auth config is invalid."},
            )

        if provided_key != expected_key:
            logger.warning(
                "Unauthorized request blocked. path=%s ip=%s",
                request.url.path,
                client_ip,
            )
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid API key."},
            )

        return await call_next(request)


class IPRateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app) -> None:
        super().__init__(app)
        self._lock = Lock()
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next) -> Response:
        if not settings.rate_limit_enabled or _is_exempt(request.url.path, settings.rate_limit_exempt_paths):
            return await call_next(request)

        now = time.time()
        window_start = now - settings.rate_limit_window_seconds
        client_ip = _get_client_ip(request)
        key = f"{client_ip}:{request.url.path}"

        with self._lock:
            bucket = self._hits[key]
            while bucket and bucket[0] < window_start:
                bucket.popleft()
            if len(bucket) >= settings.rate_limit_requests:
                logger.warning(
                    "Rate limit exceeded. path=%s ip=%s limit=%s window=%ss",
                    request.url.path,
                    client_ip,
                    settings.rate_limit_requests,
                    settings.rate_limit_window_seconds,
                )
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={"detail": "Too many requests, please retry later."},
                )
            bucket.append(now)

        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000
        if duration_ms >= settings.security_alert_slow_request_ms:
            logger.warning(
                "Slow request detected. method=%s path=%s ip=%s duration_ms=%.2f status=%s",
                request.method,
                request.url.path,
                client_ip,
                duration_ms,
                response.status_code,
            )
        return response
