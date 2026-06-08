import uuid
from typing import Callable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

from app.core.config import get_settings

settings = get_settings()

ALLOWED_CORS_HEADERS = [
    "Authorization",
    "Content-Type",
    "Accept",
    "Origin",
    "X-Requested-With",
]
EXPOSED_CORS_HEADERS = ["X-Request-Id"]


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
