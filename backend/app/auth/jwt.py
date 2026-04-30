import logging
import uuid

from jose import JWTError, jwt

from app.config import settings

logger = logging.getLogger(__name__)

ALGORITHM = "HS256"


def verify_supabase_jwt(token: str) -> uuid.UUID:
    """Decode and verify a Supabase-issued JWT. Returns the user_id on success."""
    try:
        payload = jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=[ALGORITHM],
            audience="authenticated",
        )
    except JWTError as exc:
        secret_len = len(settings.supabase_jwt_secret)
        logger.warning("JWT verification failed: %s | secret_len=%d", exc, secret_len)
        raise ValueError("Invalid or expired token") from exc

    sub = payload.get("sub")
    if not sub:
        raise ValueError("Token missing subject claim")

    try:
        return uuid.UUID(str(sub))
    except ValueError as exc:
        raise ValueError("Token subject is not a valid UUID") from exc
