# Prompt Master API

Stateless FastAPI backend: **Supabase JWT verification** + **prompt generation**. No database.

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/health` | No | Liveness check |
| POST | `/prompts/generate` | Bearer (Supabase JWT) | Generate a business prompt |
| GET | `/docs` | No | Swagger UI |

Login happens in the **Flutter app** via Supabase Google OAuth; this API only validates the access token.

## Local run

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Flutter web must call the API from an origin allowed by CORS (localhost / 127.0.0.1 with any port is allowed by default regex).

## Environment

| Variable | Description |
|----------|-------------|
| `SUPABASE_URL` | Your Supabase project URL |
| `CORS_ALLOWED_ORIGINS` | Extra comma-separated origins (production frontend URL) |
| `CORS_ALLOWED_ORIGIN_REGEX` | Local dev pattern (default covers Flutter web ports) |
| `RATE_LIMIT_PROMPT_GENERATE` | e.g. `30/hour` |

## Docker

```bash
docker compose up --build
```

## Structure

```text
app/
├── auth/       # Supabase JWKS JWT verification
├── prompts/    # Schemas, templates, generate service + route
├── core/       # Config, logging, OpenAPI, request size limit
└── base.py     # FastAPI app + CORS
main.py
```
