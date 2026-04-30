# mypy: disable-error-code="misc,arg-type,no-untyped-call,import-untyped,unused-ignore"
import logging
import uuid
from typing import Any

import httpx
from jose import JWTError, jwt

from app.config import settings

logger = logging.getLogger(__name__)

_jwks_cache: list[dict[str, Any]] | None = None


def _get_jwks() -> list[dict[str, Any]]:
    global _jwks_cache
    if _jwks_cache is not None:
        return _jwks_cache
    url = f"{settings.supabase_url}/auth/v1/.well-known/jwks.json"
    resp = httpx.get(url, timeout=10)
    resp.raise_for_status()
    _jwks_cache = resp.json().get("keys", [])
    logger.info("Loaded %d JWKS keys from Supabase", len(_jwks_cache))
    return _jwks_cache


def _build_key(jwk: dict[str, Any]) -> object:
    """Construct a jose key object from a JWK dict."""
    kty: str = jwk.get("kty", "")
    alg: str = jwk.get("alg", "ES256")
    # Import here to avoid top-level type issues with jose's untyped backends
    from jose.backends import ECKey, RSAKey  # type: ignore[import-untyped]
    if kty == "EC":
        return ECKey(jwk, algorithm=alg)  # type: ignore[no-untyped-call]
    return RSAKey(jwk, algorithm=alg)  # type: ignore[no-untyped-call]


def verify_supabase_jwt(token: str) -> uuid.UUID:
    """Decode and verify a Supabase-issued JWT. Returns the user_id on success."""
    try:
        header = jwt.get_unverified_header(token)
    except JWTError as exc:
        raise ValueError("Invalid token header") from exc

    alg: str = header.get("alg", "")

    try:
        if alg in ("RS256", "ES256"):
            jwks = _get_jwks()
            kid: str | None = header.get("kid")
            candidates = [k for k in jwks if k.get("kid") == kid] if kid else jwks
            if not candidates:
                candidates = jwks
            last_exc: Exception = ValueError("No matching JWKS key")
            for jwk in candidates:
                try:
                    key = _build_key(jwk)
                    payload: dict[str, Any] = jwt.decode(  # type: ignore[arg-type]
                        token,
                        key,
                        algorithms=[alg],
                        audience="authenticated",
                    )
                    break
                except JWTError as exc:
                    last_exc = exc
            else:
                raise last_exc
        else:
            payload = jwt.decode(
                token,
                settings.supabase_jwt_secret,
                algorithms=["HS256"],
                audience="authenticated",
            )
    except Exception as exc:
        logger.warning("JWT verification failed: %s | alg=%s", exc, alg)
        raise ValueError("Invalid or expired token") from exc

    sub = payload.get("sub")
    if not sub:
        raise ValueError("Token missing subject claim")

    try:
        return uuid.UUID(str(sub))
    except ValueError as exc:
        raise ValueError("Token subject is not a valid UUID") from exc
