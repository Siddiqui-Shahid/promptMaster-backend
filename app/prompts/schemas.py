from pydantic import BaseModel, Field, field_validator, model_validator


MAX_FIELD_LENGTH = 600
MAX_NOTES_LENGTH = 1200
DEFAULT_MAX_BUDGET_INR = 200_000


class PromptGenerateRequest(BaseModel):
    business_type: str = Field(default="", max_length=120)
    business_size: str = Field(default="", max_length=120)
    location: str = Field(default="", max_length=160)
    current_process: str = Field(default="", max_length=MAX_FIELD_LENGTH)
    biggest_problem: str = Field(default="", max_length=MAX_FIELD_LENGTH)
    current_software: str = Field(default="", max_length=MAX_FIELD_LENGTH)
    target_goal: str = Field(default="", max_length=MAX_FIELD_LENGTH)
    additional_notes: str = Field(default="", max_length=MAX_NOTES_LENGTH)
    budget_min: int | None = Field(default=None, ge=0)
    budget_max: int | None = Field(default=None, ge=0)

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

    @model_validator(mode="after")
    def validate_budget_range(self) -> "PromptGenerateRequest":
        if self.budget_min is not None and self.budget_max is not None and self.budget_min > self.budget_max:
            raise ValueError("budget_min cannot be greater than budget_max")
        return self


class PromptGenerateResponse(BaseModel):
    success: bool
    business_category: str
    detected_problems: list[str]
    recommended_software: list[str]
    generated_prompt: str
    prompt_version: str
    title: str
    business_type: str
