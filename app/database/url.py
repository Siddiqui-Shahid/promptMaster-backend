"""Normalize PostgreSQL connection URLs for sync and async SQLAlchemy engines."""

from __future__ import annotations

import re

_POSTGRES_SCHEMES = (
    "postgresql+psycopg://",
    "postgresql+psycopg_async://",
)


def is_valid_postgres_url(url: str) -> bool:
    return bool(re.match(r"^postgresql\+psycopg(_async)?://", url))


def to_sync_database_url(url: str) -> str:
    if url.startswith("postgresql+psycopg_async://"):
        return url.replace("postgresql+psycopg_async://", "postgresql+psycopg://", 1)
    if url.startswith("postgresql+psycopg://"):
        return url
    raise ValueError(
        "DATABASE_URL must use postgresql+psycopg:// or postgresql+psycopg_async://"
    )


def to_async_database_url(url: str) -> str:
    if url.startswith("postgresql+psycopg://"):
        return url.replace("postgresql+psycopg://", "postgresql+psycopg_async://", 1)
    if url.startswith("postgresql+psycopg_async://"):
        return url
    raise ValueError(
        "DATABASE_URL must use postgresql+psycopg:// or postgresql+psycopg_async://"
    )
