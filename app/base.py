import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.core.openapi import configure_openapi
from app.auth.firebase_jwt import warm_jwks_cache
from app.core.security import (
    ALLOWED_CORS_HEADERS,
    EXPOSED_CORS_HEADERS,
    RequestIdMiddleware,
    RequestSizeLimitMiddleware,
    SecurityHeadersMiddleware,
    validate_security_settings,
)
from app.prompts.router import limiter, router as prompts_router

settings = get_settings()
configure_logging()
validate_security_settings()
logger = logging.getLogger("app.api")

_docs_url = "/docs" if settings.enable_openapi else None
_redoc_url = "/redoc" if settings.enable_openapi else None
_openapi_url = "/openapi.json" if settings.enable_openapi else None


@asynccontextmanager
async def lifespan(_app: FastAPI):
    warm_jwks_cache()
    yield


app = FastAPI(
    title="Prompt Master API",
    description="Stateless API: Firebase JWT auth and business prompt generation.",
    version="1.1.0",
    docs_url=_docs_url,
    redoc_url=_redoc_url,
    openapi_url=_openapi_url,
    lifespan=lifespan,
)
configure_openapi(app)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(SlowAPIMiddleware)
app.add_middleware(RequestSizeLimitMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestIdMiddleware)

# CORS must be outermost (added last) so OPTIONS preflight is handled before other middleware.
_cors_kwargs: dict = {
    "allow_origins": [o.strip() for o in settings.cors_allowed_origins.split(",") if o.strip()],
    "allow_credentials": True,
    "allow_methods": ["GET", "POST", "OPTIONS"],
    "allow_headers": ALLOWED_CORS_HEADERS,
    "expose_headers": EXPOSED_CORS_HEADERS,
}
if settings.cors_allowed_origin_regex:
    _cors_kwargs["allow_origin_regex"] = settings.cors_allowed_origin_regex

app.add_middleware(CORSMiddleware, **_cors_kwargs)

app.include_router(prompts_router)


@app.get("/health", tags=["health"])
@limiter.exempt
async def health(request: Request) -> dict[str, str]:
    return {"status": "ok"}


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    logger.exception(
        "unhandled error on %s %s",
        request.method,
        request.url.path,
        extra={"event": "unhandled_error", "request_id": request_id},
    )
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
