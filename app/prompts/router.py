import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import fastapi_users
from app.database.models import User
from app.database.session import get_async_session

from .schemas import (
    PromptDetailResponse,
    PromptGenerateRequest,
    PromptGenerateResponse,
    PromptSummaryResponse,
)
from .service import prompt_service


router = APIRouter(prefix="/prompts", tags=["prompts"])
logger = logging.getLogger("app.prompts")


@router.post("/generate", response_model=PromptGenerateResponse)
async def generate_prompt(
    payload: PromptGenerateRequest,
    user: User = Depends(fastapi_users.current_user(active=True)),
    session: AsyncSession = Depends(get_async_session),
) -> PromptGenerateResponse:
    try:
        result = await prompt_service.generate_and_store(session=session, user=user, request=payload)
        return PromptGenerateResponse(**result)
    except HTTPException:
        raise
    except ValueError as exc:
        logger.warning("prompt generation validation failed", extra={"event": "prompt_generate_validation_error"})
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("prompt generation failed", extra={"event": "prompt_generate_error"})
        raise HTTPException(status_code=500, detail="Prompt generation failed") from exc


@router.get("", response_model=list[PromptSummaryResponse])
async def list_prompts(
    user: User = Depends(fastapi_users.current_user(active=True)),
    session: AsyncSession = Depends(get_async_session),
) -> list[PromptSummaryResponse]:
    prompts = await prompt_service.list_user_prompts(session=session, user=user)
    return [
        PromptSummaryResponse(id=item.id, title=item.title, created_at=item.created_at)
        for item in prompts
    ]


@router.get("/{prompt_id}", response_model=PromptDetailResponse)
async def get_prompt(
    prompt_id: int,
    user: User = Depends(fastapi_users.current_user(active=True)),
    session: AsyncSession = Depends(get_async_session),
) -> PromptDetailResponse:
    if prompt_id <= 0:
        raise HTTPException(status_code=400, detail="Invalid prompt_id")

    prompt = await prompt_service.get_user_prompt(session=session, user=user, prompt_id=prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")

    return PromptDetailResponse(
        id=prompt.id,
        title=prompt.title,
        business_type=prompt.business_type,
        generated_prompt=prompt.generated_prompt,
        created_at=prompt.created_at,
        expires_at=prompt.expires_at,
    )
