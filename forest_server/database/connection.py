from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from forest_server.config import get_settings
from forest_server.database.migrate import apply_migrations

_engine: AsyncEngine | None = None
_sessions: async_sessionmaker[AsyncSession] | None = None


async def init_database() -> None:
    global _engine, _sessions
    await close_database()
    engine = create_async_engine(get_settings().forest_database_url, pool_pre_ping=True)
    try:
        await apply_migrations(engine)
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception:
        await engine.dispose()
        raise
    _engine = engine
    _sessions = async_sessionmaker(engine, expire_on_commit=False)


async def close_database() -> None:
    global _engine, _sessions
    engine = _engine
    _engine = None
    _sessions = None
    if engine is not None:
        await engine.dispose()


@asynccontextmanager
async def get_session() -> AsyncIterator[AsyncSession]:
    if _sessions is None:
        raise RuntimeError("database is not initialized")
    async with _sessions() as session:
        yield session
