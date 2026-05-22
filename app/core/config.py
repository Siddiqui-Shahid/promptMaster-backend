import os
from functools import lru_cache
from dotenv import load_dotenv

from app.database.url import normalize_database_url

load_dotenv()


class Settings:
    def __init__(self) -> None:
        self.app_env = os.getenv("APP_ENV", "development")
        self.app_host = os.getenv("APP_HOST", "0.0.0.0")
        self.app_port = int(os.getenv("APP_PORT", "8000"))

        self.database_url = normalize_database_url(
            os.getenv(
                "DATABASE_URL",
                "postgresql+psycopg://postgres:postgres@localhost:5432/prompt_platform",
            )
        )

        self.jwt_secret = os.getenv("JWT_SECRET", "change-me-in-production")
        self.jwt_lifetime_seconds = int(os.getenv("JWT_LIFETIME_SECONDS", "3600"))

        self.cors_allowed_origins = os.getenv(
            "CORS_ALLOWED_ORIGINS",
            "http://localhost,http://127.0.0.1,http://localhost:8000,http://127.0.0.1:8000",
        )
        self.cors_allowed_origin_regex = os.getenv(
            "CORS_ALLOWED_ORIGIN_REGEX",
            r"http://(localhost|127\.0\.0\.1)(:\d+)?$",
        )
        self.max_request_size_bytes = int(os.getenv("MAX_REQUEST_SIZE_BYTES", "2097152"))
        self.prompt_generate_rate_limit = os.getenv("RATE_LIMIT_PROMPT_GENERATE", "10/hour")
        self.auth_rate_limit = os.getenv("RATE_LIMIT_AUTH", "20/minute")
        self.general_rate_limit = os.getenv("RATE_LIMIT_GENERAL", "100/minute")
        self.imagekit_private_key = os.getenv("IMAGEKIT_PRIVATE_KEY", "")
        self.imagekit_url_endpoint = os.getenv("IMAGEKIT_URL_ENDPOINT", "")


@lru_cache
def get_settings() -> Settings:
    return Settings()
