# PromptMaster Backend

Production-ready FastAPI backend for a prompt orchestration platform.

| Repo | URL |
|------|-----|
| **This API** | [promptMaster-backend](https://github.com/Siddiqui-Shahid/promptMaster-backend) |
| **Flutter app** | [promptMaster-frontend](https://github.com/Siddiqui-Shahid/promptMaster-frontend) |
| **Monorepo** | [promptMaster](https://github.com/Siddiqui-Shahid/promptMaster) |

## Overview
- FastAPI API-only backend
- PostgreSQL via SQLAlchemy (`postgresql+psycopg`)
- JWT auth using `fastapi-users`
- Dockerized backend + PostgreSQL
- Frontend is maintained separately (`/frontend` is not part of backend container build)

## Project Structure

```text
app/
├── auth/
├── prompts/
├── users/
├── core/
├── database/
├── base.py
└── buisness.py
```

## Environment Variables
Copy `.env.example` to `.env` and set secure values.

Required values:
- `DATABASE_URL` (local): `postgresql+psycopg://postgres:postgres@localhost:5432/prompt_platform`
- `JWT_SECRET=<strong-secret>`

Docker Compose sets `DATABASE_URL` to the internal `postgres` service automatically.

Optional values:
- `APP_HOST`, `APP_PORT`, `APP_ENV`
- `JWT_LIFETIME_SECONDS`
- `CORS_ALLOWED_ORIGINS`, `CORS_ALLOWED_ORIGIN_REGEX`
- `MAX_REQUEST_SIZE_BYTES`
- `RATE_LIMIT_PROMPT_GENERATE`, `RATE_LIMIT_AUTH`, `RATE_LIMIT_GENERAL`
- `IMAGEKIT_PRIVATE_KEY`, `IMAGEKIT_URL_ENDPOINT`

## Local Setup (without Docker)
1. Create PostgreSQL database and user.
2. Configure `.env` with your local DB URL.
3. Install dependencies:
   - `python -m venv .venv`
   - `source .venv/bin/activate`
   - `pip install -r requirements.txt`
4. Run API:
   - `uvicorn main:app --host 0.0.0.0 --port 8000 --reload`

## Docker Setup
1. Create `.env` from `.env.example`.
2. Start services:
   - `docker compose up --build`
3. API will be available at:
   - `http://localhost:${APP_PORT}` (default `8000`)

## PostgreSQL Notes
- PostgreSQL runs in `postgres` service.
- Persistent storage uses `postgres_data` volume.
- Backend waits for DB readiness before starting Uvicorn.
- The API uses native async PostgreSQL (`postgresql+psycopg_async://`) internally; keep `DATABASE_URL` as `postgresql+psycopg://` in `.env`.

### Troubleshooting
- **Connection refused (local):** start PostgreSQL and ensure `DATABASE_URL` uses `localhost`.
- **Connection refused (Docker):** do not point Docker `DATABASE_URL` to `localhost`; Compose uses host `postgres`.
- **Startup validation error in production:** set a strong `JWT_SECRET` and `APP_ENV=production` only when deploying.

## Rate Limiting
Rate limiting is enforced with SlowAPI-backed infrastructure:
- Prompt generation (`POST /prompts/generate`): `10/hour`
- Auth routes (`/auth/*`): `20/minute`
- General API fallback: `100/minute`

All limits are configurable through environment variables.

## Security Hardening
- CORS is environment-driven and does not use wildcard origins.
- Request payload size is capped with `MAX_REQUEST_SIZE_BYTES`.
- Secure response headers are added for browser hardening.
- Structured JSON logging includes prompt generation, auth failures, rate-limit violations, and server errors.
- Production startup validates critical security settings (`JWT_SECRET`, `DATABASE_URL`).

## Deployment (VPS)
1. Copy repository to VPS.
2. Set production `.env` values (`JWT_SECRET`, `DATABASE_URL`, DB credentials).
3. Run `docker compose up -d --build`.
4. Put a reverse proxy (Nginx/Caddy) in front for TLS and domain routing.
5. Set strict frontend origins in `CORS_ALLOWED_ORIGINS` for your production domains.

## Swagger Authentication
1. Register: `POST /auth/register` with email and password.
2. Option A — OAuth2 in Swagger: **Authorize** → `OAuth2PasswordBearer` → username = **email**, password = your password.
3. Option B — Bearer token: `POST /auth/jwt/login` (email as `username`), copy `access_token`, then **Authorize** → `BearerAuth` → paste token only (no `Bearer` prefix).

Open docs at **http://localhost:8000/docs** (not `0.0.0.0`).

## API Compatibility
All existing backend routes and auth flows are preserved. The migration only changes infrastructure/runtime configuration from SQLite to PostgreSQL.
