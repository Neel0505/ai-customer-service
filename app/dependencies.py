"""FastAPI dependency injection — DB sessions, Redis, and service singletons."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings

# ── Database Engine & Session ──────────────────────────────────────────────

settings = get_settings()

engine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_size=10,
    max_overflow=20,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield a DB session per request."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# ── Redis ──────────────────────────────────────────────────────────────────

_redis_pool: aioredis.Redis | None = None


async def init_redis() -> aioredis.Redis:
    """Create the global Redis connection pool."""
    global _redis_pool
    _redis_pool = aioredis.from_url(
        settings.redis_url,
        decode_responses=True,
        max_connections=20,
    )
    return _redis_pool


async def close_redis() -> None:
    """Close Redis pool on shutdown."""
    global _redis_pool
    if _redis_pool:
        await _redis_pool.close()
        _redis_pool = None


async def get_redis() -> aioredis.Redis:
    """Get the Redis client — used as a FastAPI dependency."""
    if _redis_pool is None:
        await init_redis()
    return _redis_pool  # type: ignore
