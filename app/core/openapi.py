from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi


def configure_openapi(app: FastAPI) -> None:
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema

        schema = get_openapi(
            title=app.title,
            version="1.0.0",
            description=app.description,
            routes=app.routes,
        )

        # Use relative server URL so Swagger always calls the host you opened in the browser.
        schema["servers"] = [{"url": "/", "description": "Current host"}]

        components = schema.setdefault("components", {})
        security_schemes = components.setdefault("securitySchemes", {})

        oauth2 = security_schemes.get("OAuth2PasswordBearer")
        if oauth2 and "flows" in oauth2:
            password_flow = oauth2["flows"].get("password", {})
            password_flow["tokenUrl"] = "/auth/jwt/login"

        security_schemes["BearerAuth"] = {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": (
                "Paste JWT only (no 'Bearer' prefix), or use OAuth2 login below. "
                "Get a token from POST /auth/jwt/login with email as username."
            ),
        }

        app.openapi_schema = schema
        return app.openapi_schema

    app.openapi = custom_openapi
