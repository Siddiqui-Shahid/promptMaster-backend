#!/usr/bin/env sh
set -e

python - <<'PY'
import os
import time

from sqlalchemy import create_engine, text

from app.core.db_url import resolve_database_url_from_env, to_sync_database_url

raw_url = resolve_database_url_from_env()
if not raw_url:
    raise RuntimeError(
        "DATABASE_URL is not set on this Railway service. "
        "Open your API service (not Postgres) → Variables → Add Reference → "
        "PostgreSQL → DATABASE_URL, then redeploy."
    )

url = to_sync_database_url(raw_url)

for attempt in range(30):
    try:
        engine = create_engine(url, pool_pre_ping=True)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("Database is ready")
        break
    except Exception as exc:
        if attempt == 29:
            raise RuntimeError(f"Database not reachable after 60s: {exc}") from exc
        time.sleep(2)
PY

exec uvicorn main:app --host "${APP_HOST:-0.0.0.0}" --port "${APP_PORT:-${PORT:-8000}}"
