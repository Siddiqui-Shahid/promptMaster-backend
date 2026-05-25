import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.auth.deps import AuthenticatedUser, get_current_user
from app.core.config import get_settings

from .schemas import PromptGenerateRequest, PromptGenerateResponse
from .service import prompt_service

settings = get_settings()
logger = logging.getLogger("app.prompts")


def _rate_limit_key(request: Request) -> str:
    auth = request.headers.get("authorization", "")
    if auth.startswith("Bearer "):
        token = auth[7:].strip()
        if token:
            return f"token:{token[:24]}"
    return get_remote_address(request)


limiter = Limiter(key_func=_rate_limit_key)
router = APIRouter(prefix="/prompts", tags=["prompts"])


@router.post("/generate", response_model=PromptGenerateResponse)
@limiter.limit(settings.prompt_generate_rate_limit)
async def generate_prompt(
    request: Request,
    payload: PromptGenerateRequest,
    _user: AuthenticatedUser = Depends(get_current_user),
) -> PromptGenerateResponse:
    try:
        result = prompt_service.generate(request=payload)
        logger.info("prompt generated", extra={"event": "prompt_generated"})
        return PromptGenerateResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("prompt generation failed")
        raise HTTPException(status_code=500, detail="Prompt generation failed") from exc
