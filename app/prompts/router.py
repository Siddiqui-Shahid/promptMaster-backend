import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.auth.deps import AuthenticatedUser, get_current_user
from app.core.config import get_settings
from app.core.logging import hash_user_id

from .schemas import PromptGenerateRequest, PromptGenerateResponse
from .service import prompt_service

settings = get_settings()
logger = logging.getLogger("app.prompts")


def _rate_limit_key(request: Request) -> str:
    user_id = getattr(request.state, "user_id", None)
    if user_id:
        return f"user:{user_id}"
    auth = request.headers.get("authorization", "")
    if auth.startswith("Bearer "):
        token = auth[7:].strip()
        if token:
            return f"token:{hash_user_id(token)}"
    return f"ip:{get_remote_address(request)}"


limiter = Limiter(key_func=_rate_limit_key, default_limits=[settings.global_ip_rate_limit])
router = APIRouter(prefix="/prompts", tags=["prompts"])


@router.post("/generate", response_model=PromptGenerateResponse)
@limiter.limit(settings.prompt_generate_burst_limit)
@limiter.limit(settings.prompt_generate_rate_limit)
async def generate_prompt(
    request: Request,
    payload: PromptGenerateRequest,
    user: AuthenticatedUser = Depends(get_current_user),
) -> PromptGenerateResponse:
    request_id = getattr(request.state, "request_id", None)
    user_hash = hash_user_id(str(user.id))
    try:
        result = prompt_service.generate(request=payload)
        logger.info(
            "prompt generated",
            extra={
                "event": "prompt_generated",
                "user_id_hash": user_hash,
                "request_id": request_id,
            },
        )
        return PromptGenerateResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception(
            "prompt generation failed",
            extra={
                "event": "prompt_generation_error",
                "user_id_hash": user_hash,
                "request_id": request_id,
            },
        )
        raise HTTPException(status_code=500, detail="Prompt generation failed") from exc
