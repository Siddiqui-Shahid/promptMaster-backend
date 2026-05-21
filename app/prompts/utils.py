import re


_BUSINESS_TYPE_PATTERN = re.compile(r"[^a-zA-Z0-9 ]+")
_WHITESPACE_PATTERN = re.compile(r"\s+")


def sanitize_business_type(value: str) -> tuple[str, str]:
    cleaned = _BUSINESS_TYPE_PATTERN.sub(" ", value or "")
    cleaned = _WHITESPACE_PATTERN.sub(" ", cleaned).strip()

    if not cleaned:
        cleaned = "Business"

    normalized = cleaned.lower()
    readable = " ".join(word.capitalize() for word in cleaned.split())
    return normalized, readable


def build_prompt_title(readable_business_type: str, sequence_number: int) -> str:
    return f"{readable_business_type} {sequence_number}"
