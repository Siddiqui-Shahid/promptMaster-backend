import logging
import ssl
from functools import lru_cache

import certifi
import jwt
from jwt import PyJWKClient

from app.core.config import get_settings

logger = logging.getLogger("app.auth.supabase")
settings = get_settings()


def _ssl_context() -> ssl.SSLContext:
    """Use certifi CA bundle (fixes macOS Python.org SSL: CERTIFICATE_VERIFY_FAILED)."""
    return ssl.create_default_context(cafile=certifi.where())


@lru_cache
def _jwks_client() -> PyJWKClient:
    base = settings.supabase_url.rstrip("/")
    jwks_url = f"{base}/auth/v1/.well-known/jwks.json"
    return PyJWKClient(jwks_url, cache_keys=True, ssl_context=_ssl_context())


def warm_jwks_cache() -> None:
    """Fetch JWKS at startup so misconfiguration fails immediately."""
    client = _jwks_client()
    keys = client.get_signing_keys()
    logger.info("loaded %s supabase jwks key(s)", len(keys))


def verify_supabase_access_token(token: str) -> dict:
    """Validate a Supabase Auth access token (ES256 via JWKS)."""
    signing_key = _jwks_client().get_signing_key_from_jwt(token)
    issuer = f"{settings.supabase_url.rstrip('/')}/auth/v1"
    return jwt.decode(
        token,
        signing_key.key,
        algorithms=["ES256", "RS256"],
        audience="authenticated",
        issuer=issuer,
        options={"require": ["sub", "exp"]},
    )
