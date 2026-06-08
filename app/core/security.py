import logging
import uuid
from typing import Callable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

from app.core.config import get_settings
from app.core.logging import dev_log

settings = get_settings()
http_logger = logging.getLogger("app.http")

ALLOWED_CORS_HEADERS = [
    "Authorization",
    "Content-Type",
    "Accept",
    "Origin",
    "X-Requested-With",
]
EXPOSED_CORS_HEADERS = ["X-Request-Id"]


class DevCorsHardeningMiddleware(BaseHTTPMiddleware):
    """Ensure Chrome Private Network Access headers on every response (including errors)."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        if settings.app_env == "production":
            return response
        response.headers["Access-Control-Allow-Private-Network"] = "true"
        origin = request.headers.get("origin")
        if origin and "Access-Control-Allow-Origin" not in response.headers:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log every HTTP request/response for local debugging."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = getattr(request.state, "request_id", None)
        origin = request.headers.get("origin")
        has_auth = bool(request.headers.get("authorization"))

        http_logger.info(
            "request started",
            extra={
                "event": "http_request_start",
                "method": request.method,
                "path": request.url.path,
                "origin": origin,
                "has_auth": has_auth,
                "request_id": request_id,
            },
        )
        if request.url.path != "/health":
            dev_log(
                f"→ {request.method} {request.url.path} "
                f"origin={origin or '-'} auth={'yes' if has_auth else 'NO TOKEN'}"
            )

        response = await call_next(request)

        http_logger.info(
            "request finished",
            extra={
                "event": "http_request_end",
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "request_id": request_id,
            },
        )
        if request.url.path != "/health":
            dev_log(f"← {response.status_code} {request.method} {request.url.path}")
        return response


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = request.headers.get("X-Request-Id") or str(uuid.uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-Id"] = request_id
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        if settings.app_env == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if request.method == "OPTIONS":
            return await call_next(request)

        content_length = request.headers.get("content-length")
        if content_length:
            try:
                if int(content_length) > settings.max_request_size_bytes:
                    return JSONResponse(status_code=413, content={"detail": "Request payload too large"})
            except ValueError:
                return JSONResponse(status_code=400, content={"detail": "Invalid Content-Length header"})

        if request.method in ("POST", "PUT", "PATCH"):
            body = await request.body()
            if len(body) > settings.max_request_size_bytes:
                return JSONResponse(status_code=413, content={"detail": "Request payload too large"})

            async def receive():
                return {"type": "http.request", "body": body, "more_body": False}

            request = Request(request.scope, receive)

        return await call_next(request)


def validate_security_settings() -> None:
    if not settings.firebase_project_id:
        raise RuntimeError(
            "FIREBASE_PROJECT_ID is required. Set it in backend/.env locally or as a "
            "service variable on your host (e.g. Railway → Variables). "
            "Value: Firebase Console → Project settings → General → Project ID."
        )

    placeholder_ids = ("your-firebase-project-id", "YOUR_FIREBASE_PROJECT_ID", "your_project_id")
    if settings.firebase_project_id.lower() in {p.lower() for p in placeholder_ids}:
        raise RuntimeError(
            "FIREBASE_PROJECT_ID is still a placeholder. Set it to your Firebase project ID "
            "(backend/.env locally or the host's environment variables)."
        )
