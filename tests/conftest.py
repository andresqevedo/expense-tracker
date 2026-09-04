import asyncio
from collections.abc import AsyncGenerator

import pytest
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from app.config import settings
from app.dependencies import get_db
from app.main import app

TEST_DATABASE_URL = settings.DATABASE_URL.rsplit("/", 1)[0] + "/expense_tracker_test"
_ADMIN_DATABASE_URL = settings.DATABASE_URL.rsplit("/", 1)[0] + "/postgres"
_TEST_DB_NAME = TEST_DATABASE_URL.rsplit("/", 1)[1]


async def _ensure_test_database_exists() -> None:
    admin_engine = create_async_engine(_ADMIN_DATABASE_URL, isolation_level="AUTOCOMMIT")
    try:
        async with admin_engine.connect() as conn:
            exists = await conn.scalar(
                text("SELECT 1 FROM pg_database WHERE datname = :name"), {"name": _TEST_DB_NAME}
            )
            if not exists:
                await conn.execute(text(f'CREATE DATABASE "{_TEST_DB_NAME}"'))
    finally:
        await admin_engine.dispose()


@pytest.fixture(scope="session", autouse=True)
def _prepare_test_database() -> None:
    """Real PostgreSQL, dedicated test database, migrated once per test session (Constitution Principle II)."""
    asyncio.run(_ensure_test_database_exists())

    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", TEST_DATABASE_URL)
    command.upgrade(alembic_cfg, "head")


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """One connection + outer transaction per test, rolled back after — isolates tests from each other
    even when the code under test calls session.commit() (via join_transaction_mode='create_savepoint')."""
    engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
    async with engine.connect() as connection:
        outer_transaction = await connection.begin()
        session = AsyncSession(
            bind=connection, expire_on_commit=False, join_transaction_mode="create_savepoint"
        )
        try:
            yield session
        finally:
            await session.close()
            await outer_transaction.rollback()
    await engine.dispose()


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://testserver") as async_client:
            yield async_client
    finally:
        app.dependency_overrides.pop(get_db, None)
