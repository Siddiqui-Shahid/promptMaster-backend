from pydantic import BaseModel, Field, field_validator, model_validator

MAX_TEXT_LENGTH = 100_000
DEFAULT_MAX_BUDGET_INR = 200_000

_UNSAFE_TOKENS = ("<script", "</script>", "javascript:")


def _sanitize_text(value: str) -> str:
    clean = value.replace("\x00", " ")
    lowered = clean.lower()
    if any(token in lowered for token in _UNSAFE_TOKENS):
        raise ValueError("Unsafe input detected")
    return clean


class PromptGenerateRequest(BaseModel):
    business_type: str = Field(default="", max_length=MAX_TEXT_LENGTH)
    business_size: str = Field(default="", max_length=MAX_TEXT_LENGTH)
    location: str = Field(default="", max_length=MAX_TEXT_LENGTH)
    current_process: str = Field(default="", max_length=MAX_TEXT_LENGTH)
    biggest_problem: str = Field(default="", max_length=MAX_TEXT_LENGTH)
    current_software: str = Field(default="", max_length=MAX_TEXT_LENGTH)
    target_goal: str = Field(default="", max_length=MAX_TEXT_LENGTH)
    additional_notes: str = Field(default="", max_length=MAX_TEXT_LENGTH)
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
    def sanitize_text_fields(cls, value: str) -> str:
        return _sanitize_text(value)

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
