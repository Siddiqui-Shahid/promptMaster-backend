import os
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


class Settings:
    def __init__(self) -> None:
        self.app_env = os.getenv("APP_ENV", "development")
        self.app_host = os.getenv("APP_HOST", "0.0.0.0")
        self.app_port = int(os.getenv("APP_PORT", "8000"))

        self.firebase_project_id = os.getenv("FIREBASE_PROJECT_ID", "").strip()

        self.cors_allowed_origins = os.getenv(
            "CORS_ALLOWED_ORIGINS",
            "http://localhost,http://127.0.0.1",
        )
        raw_regex = os.getenv(
            "CORS_ALLOWED_ORIGIN_REGEX",
            r"https?://(localhost|127\.0\.0\.1|\[::1\]|0\.0\.0\.0)(:\d+)?$",
        )
        self.cors_allowed_origin_regex = raw_regex.replace("\\\\", "\\") if self.app_env != "production" else None

        self.max_request_size_bytes = int(os.getenv("MAX_REQUEST_SIZE_BYTES", "2097152"))
        self.jwt_leeway_seconds = int(os.getenv("JWT_LEEWAY_SECONDS", "30"))

        self.prompt_generate_burst_limit = os.getenv("RATE_LIMIT_PROMPT_BURST", "5/minute")
        self.prompt_generate_rate_limit = os.getenv("RATE_LIMIT_PROMPT_GENERATE", "30/hour")
        self.global_ip_rate_limit = os.getenv("RATE_LIMIT_GLOBAL_IP", "120/hour")

        self.enable_openapi = os.getenv("ENABLE_OPENAPI", "").lower() in ("1", "true", "yes")
        if self.app_env == "production" and os.getenv("ENABLE_OPENAPI") is None:
            self.enable_openapi = False
        elif self.app_env != "production" and os.getenv("ENABLE_OPENAPI") is None:
            self.enable_openapi = True


@lru_cache
def get_settings() -> Settings:
    return Settings()
