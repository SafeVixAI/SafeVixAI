# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

import logging
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from core.config import get_settings


SLOW_QUERY_THRESHOLD_MS = 500
READ_REPLICA_LAG_WARNING_SECONDS = 30
logger = logging.getLogger('safevixai.database')


class Base(DeclarativeBase):
    pass


settings = get_settings()
connect_args = (
    {'prepared_statement_cache_size': 0}
    if settings.database_url.startswith('postgresql+asyncpg://')
    else {}
)


def _build_engine(database_url: str, pool_size: int = 25, max_overflow: int = 50) -> AsyncEngine:
    """Create a configured async engine for the given database URL."""
    return create_async_engine(
        database_url,
        connect_args=(
            {'prepared_statement_cache_size': 0}
            if database_url.startswith('postgresql+asyncpg://')
            else {}
        ),
        pool_pre_ping=True,
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_timeout=settings.db_pool_timeout_seconds,
        pool_recycle=settings.db_pool_recycle_seconds,
        future=True,
        echo=settings.echo_queries if hasattr(settings, 'echo_queries') else False,
    )


engine: AsyncEngine = _build_engine(
    settings.database_url,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
)

_replica_engine: AsyncEngine | None = None


def get_replica_engine() -> AsyncEngine | None:
    """Lazy-init the read replica engine if DATABASE_REPLICA_URL is configured."""
    global _replica_engine
    if _replica_engine is None:
        replica_url = getattr(settings, 'database_replica_url', None)
        if replica_url and replica_url != settings.database_url:
            _replica_engine = _build_engine(replica_url, pool_size=settings.db_pool_size, max_overflow=2)
            logger.info('Read replica engine initialized: %s', replica_url)
    return _replica_engine


@event.listens_for(engine.sync_engine, 'before_cursor_execute')
def _before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    conn._query_start_time = time.monotonic()


@event.listens_for(engine.sync_engine, 'after_cursor_execute')
def _after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    total = (time.monotonic() - conn._query_start_time) * 1000
    if total > SLOW_QUERY_THRESHOLD_MS:
        logger.warning('SLOW QUERY (%.0fms) — %s', total, statement[:200])


if get_replica_engine() is not None:
    @event.listens_for(_replica_engine.sync_engine, 'before_cursor_execute')
    def _replica_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        conn._query_start_time = time.monotonic()

    @event.listens_for(_replica_engine.sync_engine, 'after_cursor_execute')
    def _replica_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        total = (time.monotonic() - conn._query_start_time) * 1000
        if total > SLOW_QUERY_THRESHOLD_MS:
            logger.warning('SLOW QUERY ON REPLICA (%.0fms) — %s', total, statement[:200])


AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    autoflush=False,
)


if get_replica_engine() is not None:
    AsyncReadSessionLocal = async_sessionmaker(
        bind=_replica_engine,
        expire_on_commit=False,
        autoflush=False,
    )
else:
    AsyncReadSessionLocal = AsyncSessionLocal


async def get_db() -> AsyncIterator[AsyncSession]:
    """Primary database session (writes). Auto-detects replica config and falls back gracefully."""
    async with AsyncSessionLocal() as session:
        yield session


async def get_read_db() -> AsyncIterator[AsyncSession]:
    """Read-only database session. Routes to replica when DATABASE_REPLICA_URL is set."""
    if get_replica_engine() is not None:
        async with AsyncReadSessionLocal() as session:
            await session.execute(text('SET TRANSACTION READ ONLY'))
            yield session
    else:
        async with AsyncSessionLocal() as session:
            await session.execute(text('SET TRANSACTION READ ONLY'))
            yield session


# Alias used by live_tracking and other routers
get_async_session = get_db


@asynccontextmanager
async def replica_aware_session(write: bool = False):
    """Context manager that returns a write session or read session.

    Use write=True for mutations; write=False for read-only queries.
    Example:
        async with replica_aware_session(write=True) as session:
            session.add(my_obj)
            await session.commit()
    """
    if write:
        async with AsyncSessionLocal() as session:
            yield session
    else:
        async for session in get_read_db():
            yield session
            break


async def check_database() -> bool:
    if get_settings().environment == "test":
        return True
    try:
        async with engine.connect() as connection:
            await connection.execute(text('SELECT 1'))
        return True
    except Exception:
        return False


async def check_replica_database() -> bool:
    """Health check for read replica."""
    replica = get_replica_engine()
    if replica is None:
        return False
    try:
        async with replica.connect() as connection:
            await connection.execute(text('SELECT 1'))
        return True
    except Exception:
        return False
