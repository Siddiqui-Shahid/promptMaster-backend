from __future__ import annotations

import hashlib
import random
from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import User

from .classifier import classify_business
from .models import Prompt
from .schemas import PromptGenerateRequest
from .templates import (
    INDUSTRY_TEMPLATES,
    ROI_TEMPLATES,
    SALES_FRAMING_TEMPLATES,
    SYSTEM_TEMPLATES,
    TECHNICAL_RECOMMENDATION_TEMPLATES,
)
from .utils import build_prompt_title, sanitize_business_type
from .variations import VARIATIONS


PROMPT_VERSION = "v1.2.0"
MAX_PROMPT_LENGTH = 8000


class PromptService:
    def _seeded_rng(self, request: PromptGenerateRequest, salt: int = 0) -> random.Random:
        seed_basis = "|".join(
            [
                request.business_type,
                request.business_size,
                request.location,
                request.current_process,
                request.biggest_problem,
                request.current_software,
                request.target_goal,
                request.additional_notes,
                str(salt),
            ]
        )
        digest = hashlib.sha256(seed_basis.encode("utf-8")).hexdigest()
        return random.Random(int(digest[:16], 16))

    def _pick(self, rng: random.Random, bucket: str) -> str:
        return rng.choice(VARIATIONS[bucket])

    def _build_prompt(
        self,
        request: PromptGenerateRequest,
        category: str,
        detected_problems: list[str],
        recommended_software: list[str],
        rng_salt: int,
    ) -> str:
        rng = self._seeded_rng(request, rng_salt)
        sections = [
            SYSTEM_TEMPLATES["core_instruction"],
            self._pick(rng, "business_type_fragments").format(
                business_type=request.business_type,
                location=request.location,
            ),
            f"Business Size Context: {request.business_size}.",
            f"Current Process Snapshot: {request.current_process}.",
            self._pick(rng, "pain_point_fragments").format(biggest_problem=request.biggest_problem),
            f"Current Software Environment: {request.current_software}.",
            f"Primary Target Goal: {request.target_goal}.",
            INDUSTRY_TEMPLATES.get(category, INDUSTRY_TEMPLATES["general_business"]),
            f"Detected Problem Signals: {', '.join(detected_problems)}.",
            f"Potential Software Directions: {', '.join(recommended_software)}.",
            SYSTEM_TEMPLATES["delivery_guardrail"],
            self._pick(rng, "delivery_fragments"),
            self._pick(rng, "roi_fragments"),
            self._pick(rng, "tone_fragments"),
            self._pick(rng, "automation_fragments"),
            self._pick(rng, "software_fragments"),
            rng.choice(ROI_TEMPLATES),
            rng.choice(TECHNICAL_RECOMMENDATION_TEMPLATES),
            rng.choice(SALES_FRAMING_TEMPLATES),
            self._pick(rng, "expansion_fragments"),
            SYSTEM_TEMPLATES["output_contract"],
        ]

        if request.additional_notes:
            sections.append(f"Additional Business Notes: {request.additional_notes}.")

        final_prompt = "\n\n".join(sections).strip()
        if len(final_prompt) > MAX_PROMPT_LENGTH:
            final_prompt = final_prompt[:MAX_PROMPT_LENGTH].rstrip() + "\n\n[Prompt trimmed for safety constraints.]"
        return final_prompt

    async def cleanup_expired_prompts(self, session: AsyncSession) -> None:
        now = datetime.utcnow()
        await session.execute(delete(Prompt).where(Prompt.expires_at <= now))
        await session.commit()

    async def _next_title_for_user(self, session: AsyncSession, user: User, business_type_raw: str) -> tuple[str, str]:
        normalized_type, readable_type = sanitize_business_type(business_type_raw)

        result = await session.execute(
            select(Prompt.business_type).where(Prompt.user_id == user.id)
        )
        existing_types = result.scalars().all()
        existing_count = 0
        for existing in existing_types:
            existing_normalized, _ = sanitize_business_type(existing)
            if existing_normalized == normalized_type:
                existing_count += 1

        title = build_prompt_title(readable_type, existing_count + 1)
        return title, readable_type

    async def generate_and_store(self, session: AsyncSession, user: User, request: PromptGenerateRequest) -> dict:
        await self.cleanup_expired_prompts(session)

        category, detected_problems, recommended_software = classify_business(
            business_type=request.business_type,
            biggest_problem=request.biggest_problem,
            current_process=request.current_process,
        )

        prompt_count_result = await session.execute(
            select(Prompt.id).where(Prompt.user_id == user.id)
        )
        salt = len(prompt_count_result.scalars().all())

        generated_prompt = self._build_prompt(
            request=request,
            category=category,
            detected_problems=detected_problems,
            recommended_software=recommended_software,
            rng_salt=salt,
        )

        title, readable_business_type = await self._next_title_for_user(session, user, request.business_type)

        prompt_record = Prompt(
            user_id=user.id,
            title=title,
            generated_prompt=generated_prompt,
            business_type=readable_business_type,
        )
        session.add(prompt_record)
        await session.commit()
        await session.refresh(prompt_record)

        return {
            "success": True,
            "business_category": category,
            "detected_problems": detected_problems,
            "recommended_software": recommended_software,
            "generated_prompt": generated_prompt,
            "prompt_version": PROMPT_VERSION,
            "prompt_id": prompt_record.id,
            "title": prompt_record.title,
            "created_at": prompt_record.created_at.replace(tzinfo=timezone.utc),
            "expires_at": prompt_record.expires_at.replace(tzinfo=timezone.utc),
        }

    async def list_user_prompts(self, session: AsyncSession, user: User) -> list[Prompt]:
        await self.cleanup_expired_prompts(session)
        result = await session.execute(
            select(Prompt)
            .where(Prompt.user_id == user.id)
            .order_by(Prompt.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_user_prompt(self, session: AsyncSession, user: User, prompt_id: int) -> Prompt | None:
        await self.cleanup_expired_prompts(session)
        result = await session.execute(
            select(Prompt).where(Prompt.id == prompt_id, Prompt.user_id == user.id)
        )
        return result.scalars().first()


prompt_service = PromptService()
