import logging
from typing import Callable

from fastapi import Request
from limits import parse as parse_limit
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

from app.core.config import get_settings
from app.database.url import is_valid_postgres_url


logger = logging.getLogger("app.security")
settings = get_settings()


def user_or_ip_key(request: Request) -> str:
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()
        if token:
            return f"token:{token[:24]}"
    return f"ip:{get_remote_address(request)}"


limiter = Limiter(key_func=user_or_ip_key, default_limits=[settings.general_rate_limit])

DOCS_PATHS = frozenset({"/", "/docs", "/redoc", "/openapi.json"})
DOCS_PREFIXES = ("/docs/",)


def is_docs_path(path: str) -> bool:
    return path in DOCS_PATHS or path.startswith(DOCS_PREFIXES)


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > settings.max_request_size_bytes:
            return JSONResponse(status_code=413, detail="Request payload too large")
        return await call_next(request)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

        if is_docs_path(request.url.path):
            # Swagger UI loads CSS/JS from cdn.jsdelivr.net; strict CSP breaks the UI.
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "img-src 'self' data: https://fastapi.tiangolo.com; "
                "connect-src 'self'; "
                "frame-ancestors 'self';"
            )
        else:
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; frame-ancestors 'none';"
            )
        return response


class PathRateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path

        if is_docs_path(path):
            return await call_next(request)

        limit_text = settings.general_rate_limit

        if path.startswith("/auth"):
            limit_text = settings.auth_rate_limit
        elif path == "/prompts/generate":
            limit_text = settings.prompt_generate_rate_limit

        try:
            limit_item = parse_limit(limit_text)
            key = user_or_ip_key(request)
            allowed = limiter.limiter.hit(limit_item, key)
            if not allowed:
                logger.warning(
                    "rate limit exceeded",
                    extra={"event": "rate_limit_exceeded", "path": path, "method": request.method, "ip": get_remote_address(request)},
                )
                raise RateLimitExceeded(detail=f"Rate limit exceeded: {limit_text}")
        except RateLimitExceeded:
            return JSONResponse(status_code=429, content={"detail": f"Rate limit exceeded. Limit: {limit_text}"})

        return await call_next(request)


def validate_security_settings() -> None:
    if settings.app_env == "production":
        weak_secret = settings.jwt_secret in {"", "change-me-in-production", "your_secret_key_here"}
        if weak_secret:
            raise RuntimeError("JWT_SECRET must be set to a strong value in production")

        if not is_valid_postgres_url(settings.database_url):
            raise RuntimeError(
                "DATABASE_URL must use postgresql+psycopg:// in production"
            )

    if not is_valid_postgres_url(settings.database_url):
        raise RuntimeError(
            "DATABASE_URL must use postgresql+psycopg:// or postgresql+psycopg_async://"
        )
