from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

engine = create_async_engine(settings.DATABASE_URL, future=True)

async_session_maker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
