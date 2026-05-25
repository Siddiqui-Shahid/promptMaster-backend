#!/usr/bin/env sh
set -e

exec uvicorn main:app --host "${APP_HOST:-0.0.0.0}" --port "${APP_PORT:-${PORT:-8000}}"
