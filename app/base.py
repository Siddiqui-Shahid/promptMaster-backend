import os
import shutil
import tempfile
from contextlib import asynccontextmanager
import logging

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import auth_backend, fastapi_users
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.core.openapi import configure_openapi
from app.core.security import (
    PathRateLimitMiddleware,
    RequestSizeLimitMiddleware,
    SecurityHeadersMiddleware,
    limiter,
    validate_security_settings,
)
from app.database.models import Post, User
from app.database.session import create_db_and_tables, get_async_session
from app.images import imageKit
from app.prompts.router import router as prompts_router
from app.users import UserCreate, UserRead


settings = get_settings()
configure_logging()
validate_security_settings()
logger = logging.getLogger("app.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await create_db_and_tables()
    except Exception as exc:
        logger.exception(
            "database initialization failed",
            extra={"event": "database_init_failed"},
        )
        raise RuntimeError(
            "Could not connect to PostgreSQL. Check DATABASE_URL and ensure "
            "PostgreSQL is running (local: localhost:5432, Docker: host 'postgres')."
        ) from exc
    yield


app = FastAPI(
    title="Prompt-Based Business Opportunity Platform",
    description=(
        "Prompt orchestration backend that generates optimized prompts for external AI platforms. "
        "No direct AI inference is performed in this service."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)
configure_openapi(app)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.cors_allowed_origins.split(",") if origin.strip()],
    allow_origin_regex=settings.cors_allowed_origin_regex,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "Origin"],
)
app.add_middleware(RequestSizeLimitMiddleware)
app.add_middleware(PathRateLimitMiddleware)
app.add_middleware(SecurityHeadersMiddleware)


@app.middleware("http")
async def request_audit_middleware(request, call_next):
    response = await call_next(request)
    path = request.url.path
    if path == "/prompts/generate" and response.status_code < 400:
        logger.info("prompt generated", extra={"event": "prompt_generated", "path": path, "method": request.method, "status_code": response.status_code})
    if path.startswith("/auth") and response.status_code >= 400:
        logger.warning("auth failure", extra={"event": "auth_failure", "path": path, "method": request.method, "status_code": response.status_code})
    if response.status_code >= 500:
        logger.error("server error response", extra={"event": "server_error", "path": path, "method": request.method, "status_code": response.status_code})
    return response


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception(
        "unhandled server exception",
        extra={"event": "unhandled_exception", "path": request.url.path, "method": request.method},
    )
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})

app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_reset_password_router(),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_verify_router(UserRead),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_users_router(UserRead, UserCreate),
    prefix="/users",
    tags=["users"],
)

app.include_router(prompts_router)


@app.get("/", include_in_schema=False)
async def root() -> RedirectResponse:
    return RedirectResponse(url="/docs")


@app.post("/upload")
async def upload_file(
    uploadFile: UploadFile = File(...),
    caption: str = Form(""),
    user: User = Depends(fastapi_users.current_user(active=True)),
    session: AsyncSession = Depends(get_async_session),
):
    tempfile_path = None
    try:
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=os.path.splitext(uploadFile.filename)[1],
        ) as tmp:
            tempfile_path = tmp.name
            shutil.copyfileobj(uploadFile.file, tmp)

        upload_result = imageKit.files.upload(
            file=open(tempfile_path, "rb"),
            file_name=uploadFile.filename,
            folder="/uploads",
            use_unique_file_name=True,
            tags=["backend_upload"],
        )
        if upload_result.url:
            post = Post(
                user_id=user.id,
                caption=caption,
                url=upload_result.url,
                fileType="Video" if uploadFile.content_type.startswith("video/") else "Image",
                fileName=upload_result.name,
            )

            session.add(post)
            await session.commit()
            await session.refresh(post)

            return {
                "message": "File uploaded successfully",
                "post": post.to_dict(),
            }

        raise HTTPException(status_code=500, detail="File upload failed")
    except Exception as exc:
        raise HTTPException(status_code=500, detail="File upload failed") from exc
    finally:
        if tempfile_path and os.path.exists(tempfile_path):
            os.unlink(tempfile_path)
        uploadFile.file.close()


@app.get("/feed")
async def get_feed(
    limit: int = 10,
    user: User = Depends(fastapi_users.current_user(active=True)),
    session: AsyncSession = Depends(get_async_session),
):
    result = await session.execute(select(Post).order_by(Post.created_at.desc()).limit(limit))
    posts = []
    for post in result.scalars().all():
        post_dict = post.to_dict()
        post_dict["is_owner"] = post.user_id == user.id
        posts.append(post_dict)
    return posts


@app.get("/posts")
async def get_posts(
    limit: int = 10,
    user: User = Depends(fastapi_users.current_user(active=True)),
    session: AsyncSession = Depends(get_async_session),
):
    result = await session.execute(select(Post).order_by(Post.created_at.desc()).limit(limit))
    return result.scalars().all()


@app.delete("/posts/{post_id}")
async def delete_post(
    post_id: str,
    user: User = Depends(fastapi_users.current_user(active=True)),
    session: AsyncSession = Depends(get_async_session),
):
    result = await session.execute(select(Post).where(Post.id == post_id))
    post = result.scalars().first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this post")
    await session.delete(post)
    await session.commit()
    return {"message": "Post deleted successfully"}
