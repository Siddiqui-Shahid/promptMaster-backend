"""Normalize PostgreSQL connection URLs for sync and async SQLAlchemy engines."""

from __future__ import annotations

import re

_POSTGRES_SCHEMES = (
    "postgresql+psycopg://",
    "postgresql+psycopg_async://",
)

# Railway, Heroku, and other hosts often provide plain postgresql:// URLs.
_RAILWAY_STYLE_PREFIXES = (
    ("postgresql://", "postgresql+psycopg://"),
    ("postgres://", "postgresql+psycopg://"),
)


def normalize_database_url(url: str) -> str:
    """Convert provider-style URLs (e.g. Railway) to psycopg SQLAlchemy URLs."""
    normalized = url.strip()
    for source, target in _RAILWAY_STYLE_PREFIXES:
        if normalized.startswith(source):
            return normalized.replace(source, target, 1)
    return normalized


def is_valid_postgres_url(url: str) -> bool:
    normalized = normalize_database_url(url)
    return bool(re.match(r"^postgresql\+psycopg(_async)?://", normalized))


def to_sync_database_url(url: str) -> str:
    normalized = normalize_database_url(url)
    if normalized.startswith("postgresql+psycopg_async://"):
        return normalized.replace("postgresql+psycopg_async://", "postgresql+psycopg://", 1)
    if normalized.startswith("postgresql+psycopg://"):
        return normalized
    raise ValueError(
        "DATABASE_URL must use postgresql+psycopg://, postgresql+psycopg_async://, "
        "or postgresql:// (converted automatically)"
    )


def to_async_database_url(url: str) -> str:
    normalized = normalize_database_url(url)
    if normalized.startswith("postgresql+psycopg://"):
        return normalized.replace("postgresql+psycopg://", "postgresql+psycopg_async://", 1)
    if normalized.startswith("postgresql+psycopg_async://"):
        return normalized
    raise ValueError(
        "DATABASE_URL must use postgresql+psycopg://, postgresql+psycopg_async://, "
        "or postgresql:// (converted automatically)"
    )
