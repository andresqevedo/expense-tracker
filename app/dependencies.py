import uuid
from collections.abc import AsyncGenerator

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import async_session_maker
from app.models.user import User
from app.security.jwt import decode_access_token, get_token_from_request


class NotAuthenticatedError(Exception):
    """Raised when a protected route has no valid current user."""


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)) -> User:
    token = get_token_from_request(request)
    if token is None:
        raise NotAuthenticatedError()

    subject = decode_access_token(token)
    if subject is None:
        raise NotAuthenticatedError()

    try:
        user_id = uuid.UUID(subject)
    except ValueError:
        raise NotAuthenticatedError()

    user = await db.get(User, user_id)
    if user is None:
        raise NotAuthenticatedError()

    return user
