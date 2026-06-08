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

        security_schemes["BearerAuth"] = {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": (
                "Firebase ID token from the Flutter client "
                "(Authorization: Bearer <id_token>). "
                "Sign in with Google via Firebase Auth."
            ),
        }

        app.openapi_schema = schema
        return app.openapi_schema

    app.openapi = custom_openapi
