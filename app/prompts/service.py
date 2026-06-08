from __future__ import annotations

import hashlib
import random

from .classifier import classify_business
from .schemas import DEFAULT_MAX_BUDGET_INR, PromptGenerateRequest
from .templates import (
    CYFUR_CONTACT_EMAIL,
    CYFUR_WEBSITE,
    INDUSTRY_TEMPLATES,
    ROI_TEMPLATES,
    SALES_FRAMING_TEMPLATES,
    SYSTEM_TEMPLATES,
    TECHNICAL_RECOMMENDATION_TEMPLATES,
)
from .utils import build_prompt_title, sanitize_business_type
from .variations import VARIATIONS


PROMPT_VERSION = "v1.5.0"
MAX_PROMPT_LENGTH = 50_000
MAX_NOTES_IN_PROMPT = 12_000


class PromptService:
    @staticmethod
    def _has(value: str | None) -> bool:
        return bool(value and value.strip())

    def _web_search_hints(self, request: PromptGenerateRequest) -> str:
        parts = [p.strip() for p in (request.business_type, request.location) if self._has(p)]
        if not parts and self._has(request.additional_notes):
            snippet = request.additional_notes.strip().split("\n", 1)[0][:80]
            parts.append(snippet)
        query = " ".join(parts) if parts else "local MSME business India"
        return (
            f"Suggested search queries: \"{query}\", \"{query} reviews\", "
            f"\"{query} Google Maps\", \"{query} competitors\"."
        )

    def _budget_section(self, request: PromptGenerateRequest) -> str:
        if request.budget_min is not None and request.budget_max is not None:
            return (
                f"Budget Range (INR): ₹{request.budget_min:,} (minimum) to ₹{request.budget_max:,} (maximum). "
                "All development cost estimates must stay within this range."
            )
        if request.budget_min is not None:
            return (
                f"Minimum Budget (INR): ₹{request.budget_min:,}. "
                f"If no maximum was provided, cap recommendations at ₹{DEFAULT_MAX_BUDGET_INR:,} unless notes say otherwise."
            )
        if request.budget_max is not None:
            return (
                f"Maximum Budget (INR): ₹{request.budget_max:,}. "
                "All development cost estimates must stay at or below this amount."
            )
        return SYSTEM_TEMPLATES["budget_inr_default"]

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
                str(request.budget_min or ""),
                str(request.budget_max or ""),
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
        has_sparse_input = not any(
            [
                self._has(request.business_type),
                self._has(request.business_size),
                self._has(request.location),
                self._has(request.current_process),
                self._has(request.biggest_problem),
                self._has(request.current_software),
                self._has(request.target_goal),
                self._has(request.additional_notes),
            ]
        )

        sections: list[str] = [
            SYSTEM_TEMPLATES["core_instruction"],
            SYSTEM_TEMPLATES["web_research_instruction"],
            self._web_search_hints(request),
        ]

        if self._has(request.business_type) or self._has(request.location):
            business_type = request.business_type.strip() if self._has(request.business_type) else "local business"
            location = request.location.strip() if self._has(request.location) else "India"
            sections.append(
                self._pick(rng, "business_type_fragments").format(
                    business_type=business_type,
                    location=location,
                )
            )
        elif not has_sparse_input:
            sections.append("You are advising a local MSME business operating in India.")

        if self._has(request.business_size):
            sections.append(f"Business Size Context: {request.business_size.strip()}.")

        if self._has(request.current_process):
            sections.append(f"Current Process Snapshot: {request.current_process.strip()}.")

        if self._has(request.biggest_problem):
            sections.append(
                self._pick(rng, "pain_point_fragments").format(biggest_problem=request.biggest_problem.strip())
            )

        if self._has(request.current_software):
            sections.append(f"Current Software Environment: {request.current_software.strip()}.")

        if self._has(request.target_goal):
            sections.append(f"Primary Target Goal: {request.target_goal.strip()}.")

        sections.append(self._budget_section(request))
        sections.append(INDUSTRY_TEMPLATES.get(category, INDUSTRY_TEMPLATES["general_business"]))
        sections.append(f"Detected Problem Signals: {', '.join(detected_problems)}.")
        sections.append(f"Potential Software Directions: {', '.join(recommended_software)}.")

        if has_sparse_input:
            sections.append(SYSTEM_TEMPLATES["sparse_input_guardrail"])
        else:
            sections.append(
                "Combine the business details below with your web research. Do not invent facts that contradict cited sources."
            )

        sections.extend(
            [
                SYSTEM_TEMPLATES["cyfur_company_context"],
                SYSTEM_TEMPLATES["cyfur_delivery_scope"],
                SYSTEM_TEMPLATES["cyfur_delivery_limits"],
                SYSTEM_TEMPLATES["thread_guardrails"],
                SYSTEM_TEMPLATES["email_on_request_instruction"],
                SYSTEM_TEMPLATES["delivery_guardrail"],
                self._pick(rng, "delivery_fragments"),
                self._pick(rng, "roi_fragments"),
                self._pick(rng, "tone_fragments"),
                self._pick(rng, "automation_fragments"),
                self._pick(rng, "software_fragments"),
                rng.choice(ROI_TEMPLATES),
                rng.choice(TECHNICAL_RECOMMENDATION_TEMPLATES),
                rng.choice(SALES_FRAMING_TEMPLATES),
                SYSTEM_TEMPLATES["sales_cta"],
                self._pick(rng, "expansion_fragments"),
                SYSTEM_TEMPLATES["output_contract"],
                (
                    f"Reminder: Cyfur contact {CYFUR_CONTACT_EMAIL} | {CYFUR_WEBSITE}. "
                    "User may follow up in this chat with: 'write email' to get outreach copy."
                ),
            ]
        )

        if self._has(request.additional_notes):
            notes = request.additional_notes.strip()
            if len(notes) > MAX_NOTES_IN_PROMPT:
                notes = (
                    f"{notes[:MAX_NOTES_IN_PROMPT].rstrip()}… "
                    f"[{len(request.additional_notes)} chars pasted; truncated for prompt length]"
                )
            sections.append(f"Additional Business Notes: {notes}")

        final_prompt = "\n\n".join(sections).strip()
        if len(final_prompt) > MAX_PROMPT_LENGTH:
            final_prompt = final_prompt[:MAX_PROMPT_LENGTH].rstrip() + "\n\n[Prompt trimmed for safety constraints.]"
        return final_prompt

    def generate(self, request: PromptGenerateRequest) -> dict:
        category, detected_problems, recommended_software = classify_business(
            business_type=request.business_type,
            biggest_problem=request.biggest_problem,
            current_process=request.current_process,
        )

        seed_source = request.business_type or request.biggest_problem or request.target_goal or "general"
        salt = int(hashlib.sha256(seed_source.encode()).hexdigest()[:8], 16)
        generated_prompt = self._build_prompt(
            request=request,
            category=category,
            detected_problems=detected_problems,
            recommended_software=recommended_software,
            rng_salt=salt,
        )

        _, readable_business_type = sanitize_business_type(request.business_type)
        title = build_prompt_title(readable_business_type, 1)

        return {
            "success": True,
            "business_category": category,
            "detected_problems": detected_problems,
            "recommended_software": recommended_software,
            "generated_prompt": generated_prompt,
            "prompt_version": PROMPT_VERSION,
            "title": title,
            "business_type": readable_business_type,
        }


prompt_service = PromptService()
