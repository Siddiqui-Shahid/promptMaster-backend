import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.core.openapi import configure_openapi
from app.auth.supabase_jwt import warm_jwks_cache
from app.core.security import RequestSizeLimitMiddleware, validate_security_settings
from app.prompts.router import limiter, router as prompts_router

settings = get_settings()
configure_logging()
validate_security_settings()
logger = logging.getLogger("app.api")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    warm_jwks_cache()
    yield


app = FastAPI(
    title="Prompt Master API",
    description="Stateless API: Supabase JWT auth and business prompt generation.",
    version="1.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)
configure_openapi(app)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(RequestSizeLimitMiddleware)

# CORS must be outermost (added last) so OPTIONS preflight is handled before other middleware.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_allowed_origins.split(",") if o.strip()],
    allow_origin_regex=settings.cors_allowed_origin_regex,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

app.include_router(prompts_router)


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
