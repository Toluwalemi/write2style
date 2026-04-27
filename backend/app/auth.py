import logging
from functools import lru_cache

import jwt
from fastapi import HTTPException, Request, status
from jwt import PyJWKClient

from .config import settings
from .logging_config import user_id_var

log = logging.getLogger("app.auth")


@lru_cache(maxsize=1)
def _jwks_client() -> PyJWKClient:
    return PyJWKClient(settings.clerk_jwks_url)


def current_user(request: Request) -> str:
    auth_header = request.headers.get("authorization", "")
    if not auth_header.lower().startswith("bearer "):
        log.warning("auth_missing_bearer")
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing bearer token")

    token = auth_header.split(" ", 1)[1].strip()
    try:
        signing_key = _jwks_client().get_signing_key_from_jwt(token).key
        decoded = jwt.decode(
            token,
            signing_key,
            algorithms=["RS256"],
            issuer=settings.clerk_issuer,
            options={"verify_aud": False},
        )
    except jwt.PyJWTError as exc:
        log.warning("auth_invalid_token", extra={"reason": str(exc)})
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, f"Invalid token: {exc}") from exc

    user_id = decoded.get("sub")
    if not user_id:
        log.warning("auth_missing_subject")
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token missing subject")
    user_id_var.set(user_id)
    return user_id
