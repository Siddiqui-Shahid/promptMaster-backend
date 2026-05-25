from typing import Callable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

from app.core.config import get_settings

settings = get_settings()


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if request.method == "OPTIONS":
            return await call_next(request)

        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > settings.max_request_size_bytes:
            return JSONResponse(status_code=413, content={"detail": "Request payload too large"})
        return await call_next(request)


def validate_security_settings() -> None:
    if settings.app_env == "production" and not settings.supabase_url.startswith("https://"):
        raise RuntimeError("SUPABASE_URL must use https in production")

    placeholder_hosts = ("your-project-ref", "example.com", "localhost.supabase")
    if any(marker in settings.supabase_url for marker in placeholder_hosts):
        raise RuntimeError(
            "SUPABASE_URL in backend/.env is still a placeholder. "
            "Set it to your Supabase project URL (same as the Flutter SUPABASE_URL)."
        )
