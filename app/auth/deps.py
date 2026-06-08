import logging
from dataclasses import dataclass

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClientConnectionError

from app.core.logging import dev_log, hash_user_id

from .firebase_jwt import verify_firebase_id_token

logger = logging.getLogger("app.auth")
_bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class AuthenticatedUser:
    id: str
    email: str | None


def _client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> AuthenticatedUser:
    request_id = getattr(request.state, "request_id", None)
    ip = _client_ip(request)

    if credentials is None or not credentials.credentials:
        dev_log(f"AUTH FAIL {request.method} {request.url.path} — no Bearer token (sign in on frontend first)")
        logger.warning(
            "missing bearer token",
            extra={
                "event": "auth_failure",
                "request_id": request_id,
                "ip": ip,
                "path": request.url.path,
                "method": request.method,
            },
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    try:
        claims = verify_firebase_id_token(token)
    except PyJWKClientConnectionError as exc:
        logger.error(
            "cannot fetch firebase jwks: %s",
            exc,
            extra={"event": "auth_jwks_error", "request_id": request_id, "ip": ip},
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Cannot verify login token: backend cannot reach Google JWKS. "
                "Check FIREBASE_PROJECT_ID in backend/.env matches your Firebase project."
            ),
        ) from exc
    except jwt.ExpiredSignatureError:
        dev_log(f"AUTH FAIL {request.method} {request.url.path} — Firebase token expired")
        logger.warning(
            "expired firebase token",
            extra={
                "event": "auth_failure",
                "request_id": request_id,
                "ip": ip,
                "path": request.url.path,
            },
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None
    except jwt.InvalidTokenError:
        dev_log(f"AUTH FAIL {request.method} {request.url.path} — invalid Firebase token (project ID mismatch?)")
        logger.warning(
            "invalid firebase token",
            extra={
                "event": "auth_failure",
                "request_id": request_id,
                "ip": ip,
                "path": request.url.path,
            },
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None

    user_id = str(claims["sub"])
    if not user_id:
        logger.warning(
            "invalid user id in token",
            extra={"event": "auth_failure", "request_id": request_id, "ip": ip},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user id in token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    email = claims.get("email")

    request.state.user_id = user_id
    user_hash = hash_user_id(user_id)
    dev_log(f"AUTH OK {request.method} {request.url.path} user_hash={user_hash}")
    logger.info(
        "authenticated request",
        extra={
            "event": "auth_success",
            "user_id_hash": user_hash,
            "request_id": request_id,
            "ip": ip,
            "path": request.url.path,
        },
    )

    return AuthenticatedUser(id=user_id, email=email)
