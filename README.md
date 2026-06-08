# Prompt Master API

Stateless FastAPI backend: **Firebase JWT verification** + **prompt generation**. No database.

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/health` | No | Liveness check |
| POST | `/prompts/generate` | Bearer (Firebase ID token) | Generate a business prompt |
| GET | `/docs` | No | Swagger UI |

Login happens in the **Flutter app** via Firebase Google sign-in; this API only validates the ID token.

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
| `FIREBASE_PROJECT_ID` | Your Firebase project ID |
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
├── auth/       # Firebase JWKS JWT verification
├── prompts/    # Schemas, templates, generate service + route
├── core/       # Config, logging, OpenAPI, request size limit
└── base.py     # FastAPI app + CORS
main.py
```
