from datetime import datetime, timedelta, timezone

from fastapi import Request
from jose import JWTError, jwt

from app.config import settings

ACCESS_TOKEN_COOKIE_NAME = "access_token"
ACCESS_TOKEN_EXPIRE_MINUTES = 24 * 60  # 24h, per spec Clarifications (Session 2026-09-03)


def create_access_token(subject: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> str | None:
    """Return the subject (user id) encoded in the token, or None if invalid/expired."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        return None
    return payload.get("sub")


def get_token_from_request(request: Request) -> str | None:
    """Read the JWT from the HttpOnly cookie, falling back to an Authorization: Bearer header."""
    token = request.cookies.get(ACCESS_TOKEN_COOKIE_NAME)
    if token:
        return token

    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header.removeprefix("Bearer ").strip()

    return None
