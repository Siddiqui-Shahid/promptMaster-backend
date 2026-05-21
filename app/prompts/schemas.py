from datetime import datetime

from pydantic import BaseModel, Field, field_validator


MAX_FIELD_LENGTH = 600
MAX_NOTES_LENGTH = 1200


class PromptGenerateRequest(BaseModel):
    business_type: str = Field(..., min_length=1, max_length=120)
    business_size: str = Field(..., min_length=2, max_length=120)
    location: str = Field(..., min_length=2, max_length=160)
    current_process: str = Field(..., min_length=10, max_length=MAX_FIELD_LENGTH)
    biggest_problem: str = Field(..., min_length=10, max_length=MAX_FIELD_LENGTH)
    current_software: str = Field(..., min_length=2, max_length=MAX_FIELD_LENGTH)
    target_goal: str = Field(..., min_length=10, max_length=MAX_FIELD_LENGTH)
    additional_notes: str = Field(default="", max_length=MAX_NOTES_LENGTH)

    @field_validator(
        "business_type",
        "business_size",
        "location",
        "current_process",
        "biggest_problem",
        "current_software",
        "target_goal",
        "additional_notes",
    )
    @classmethod
    def sanitize_text(cls, value: str) -> str:
        clean = " ".join(value.replace("\x00", " ").split())
        lowered = clean.lower()
        if any(token in lowered for token in ["<script", "</script>", "javascript:"]):
            raise ValueError("Unsafe input detected")
        return clean


class PromptSummaryResponse(BaseModel):
    id: int
    title: str
    created_at: datetime


class PromptDetailResponse(BaseModel):
    id: int
    title: str
    business_type: str
    generated_prompt: str
    created_at: datetime
    expires_at: datetime


class PromptGenerateResponse(BaseModel):
    success: bool
    business_category: str
    detected_problems: list[str]
    recommended_software: list[str]
    generated_prompt: str
    prompt_version: str
    prompt_id: int
    title: str
    created_at: datetime
    expires_at: datetime
