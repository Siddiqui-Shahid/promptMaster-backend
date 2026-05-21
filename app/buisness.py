from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import User
from app.database.session import get_async_session
from app.prompts.schemas import PromptGenerateRequest, PromptGenerateResponse
from app.prompts.service import prompt_service
from app.auth import fastapi_users


router = APIRouter(tags=["business-prompts"])


@router.post("/ai/business-ideas", response_model=PromptGenerateResponse)
async def generate_business_prompt(
    payload: PromptGenerateRequest,
    user: User = Depends(fastapi_users.current_user(active=True)),
    session: AsyncSession = Depends(get_async_session),
) -> PromptGenerateResponse:
    """
    Backward-compatible endpoint.
    This platform generates prompts only; users run prompts on their preferred AI provider.
    """
    result = await prompt_service.generate_and_store(session=session, user=user, request=payload)
    return PromptGenerateResponse(**result)
