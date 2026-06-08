import hashlib
import json
import logging
import re
import sys
from datetime import datetime, timezone

_BEARER_RE = re.compile(r"Bearer\s+[A-Za-z0-9\-_\.=]+", re.IGNORECASE)
_JWT_RE = re.compile(r"eyJ[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+")
_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")


def redact_sensitive(text: str) -> str:
    if not text:
        return text
    redacted = _BEARER_RE.sub("Bearer [REDACTED]", text)
    redacted = _JWT_RE.sub("[REDACTED_JWT]", redacted)
    redacted = _EMAIL_RE.sub("[REDACTED_EMAIL]", redacted)
    return redacted


def hash_user_id(user_id: str) -> str:
    return hashlib.sha256(user_id.encode()).hexdigest()[:16]


def dev_log(message: str) -> None:
    """Human-readable line in the uvicorn terminal (filter with [BACKEND])."""
    print(f"[BACKEND] {message}", flush=True)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": redact_sensitive(record.getMessage()),
        }
        if record.exc_info:
            payload["exception"] = redact_sensitive(self.formatException(record.exc_info))
        for key in (
            "event",
            "path",
            "method",
            "status_code",
            "user_id_hash",
            "ip",
            "request_id",
            "origin",
            "has_auth",
        ):
            value = getattr(record, key, None)
            if value is not None:
                payload[key] = value
        return json.dumps(payload)


def configure_logging() -> None:
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root.handlers = [handler]
