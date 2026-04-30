import logging
import uuid

import httpx
from jose import JWTError, jwt

from app.config import settings

logger = logging.getLogger(__name__)

# Cached JWKS public keys (fetched once at startup)
_jwks_cache: list[dict] | None = None  # type: ignore[type-arg]


def _get_jwks() -> list[dict]:  # type: ignore[type-arg]
    global _jwks_cache
    if _jwks_cache is not None:
        return _jwks_cache
    url = f"{settings.supabase_url}/auth/v1/.well-known/jwks.json"
    resp = httpx.get(url, timeout=10)
    resp.raise_for_status()
    _jwks_cache = resp.json().get("keys", [])
    logger.info("Loaded %d JWKS keys from Supabase", len(_jwks_cache))
    return _jwks_cache


def verify_supabase_jwt(token: str) -> uuid.UUID:
    """Decode and verify a Supabase-issued JWT. Returns the user_id on success."""
    # Decode header without verification to check algorithm
    try:
        header = jwt.get_unverified_header(token)
    except JWTError as exc:
        raise ValueError("Invalid token header") from exc

    alg = header.get("alg", "")

    try:
        if alg == "RS256":
            # Verify using Supabase JWKS public keys
            keys = _get_jwks()
            kid = header.get("kid")
            # Try matching key by kid, fall back to trying all keys
            candidates = [k for k in keys if k.get("kid") == kid] if kid else keys
            if not candidates:
                candidates = keys
            last_exc: Exception = ValueError("No JWKS keys available")
            for jwk in candidates:
                try:
                    payload = jwt.decode(
                        token,
                        jwk,
                        algorithms=["RS256"],
                        audience="authenticated",
                    )
                    break
                except JWTError as exc:
                    last_exc = exc
            else:
                raise last_exc
        else:
            # HS256 fallback for older Supabase projects
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
