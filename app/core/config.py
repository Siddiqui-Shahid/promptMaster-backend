import os
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


class Settings:
    def __init__(self) -> None:
        self.app_env = os.getenv("APP_ENV", "development")
        self.app_host = os.getenv("APP_HOST", "0.0.0.0")
        self.app_port = int(os.getenv("APP_PORT", "8000"))

        self.supabase_url = os.getenv(
            "SUPABASE_URL",
            "https://gmpvqdtspyxruunscvpc.supabase.co",
        ).rstrip("/")

        self.cors_allowed_origins = os.getenv(
            "CORS_ALLOWED_ORIGINS",
            "http://localhost,http://127.0.0.1",
        )
        # Match any localhost / loopback port (Flutter web uses random ports).
        raw_regex = os.getenv(
            "CORS_ALLOWED_ORIGIN_REGEX",
            r"https?://(localhost|127\.0\.0\.1|\[::1\]|0\.0\.0\.0)(:\d+)?$",
        )
        # .env copies often double-escape backslashes; normalize so the regex still works.
        self.cors_allowed_origin_regex = raw_regex.replace("\\\\", "\\")

        self.max_request_size_bytes = int(os.getenv("MAX_REQUEST_SIZE_BYTES", "2097152"))
        self.prompt_generate_rate_limit = os.getenv("RATE_LIMIT_PROMPT_GENERATE", "30/hour")


@lru_cache
def get_settings() -> Settings:
    return Settings()
