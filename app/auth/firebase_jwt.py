import logging
import ssl
from functools import lru_cache

import certifi
import jwt
from jwt import PyJWKClient

from app.core.config import get_settings

logger = logging.getLogger("app.auth.firebase")
settings = get_settings()

FIREBASE_JWKS_URL = (
    "https://www.googleapis.com/service_accounts/v1/jwk/securetoken@system.gserviceaccount.com"
)


def _ssl_context() -> ssl.SSLContext:
    """Use certifi CA bundle (fixes macOS Python.org SSL: CERTIFICATE_VERIFY_FAILED)."""
    return ssl.create_default_context(cafile=certifi.where())


@lru_cache
def _jwks_client() -> PyJWKClient:
    return PyJWKClient(FIREBASE_JWKS_URL, cache_keys=True, ssl_context=_ssl_context())


def warm_jwks_cache() -> None:
    """Fetch JWKS at startup so misconfiguration fails immediately."""
    client = _jwks_client()
    keys = client.get_signing_keys()
    logger.info("loaded %s firebase jwks key(s)", len(keys))


def verify_firebase_id_token(token: str) -> dict:
    """Validate a Firebase Auth ID token (RS256 via Google JWKS)."""
    signing_key = _jwks_client().get_signing_key_from_jwt(token)
    project_id = settings.firebase_project_id
    issuer = f"https://securetoken.google.com/{project_id}"
    claims = jwt.decode(
        token,
        signing_key.key,
        algorithms=["RS256"],
        audience=project_id,
        issuer=issuer,
        leeway=settings.jwt_leeway_seconds,
        options={"require": ["sub", "exp", "iat"]},
    )
    return claims
