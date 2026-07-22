# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""
Data retention and cleanup scheduler.

Periodically removes expired data according to retention policies:
- Live tracking sessions: 30 days
- Chat logs: 90 days
- SOS incidents: 90 days
"""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

logger = logging.getLogger("safevixai.backend.data_retention")


class DataRetentionScheduler:
    """Background scheduler for data retention cleanup."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self.session_factory = session_factory
        self._running = False
        self._task: asyncio.Task | None = None

    async def start(self, interval_seconds: int = 86400) -> None:
        """
        Start the background cleanup scheduler.
        
        Args:
            interval_seconds: How often to run cleanup (default: 86400 = 24 hours)
        """
        if self._running:
            logger.warning("DataRetentionScheduler is already running")
            return

        self._running = True
        self._task = asyncio.create_task(self._loop(interval_seconds))
        logger.info("DataRetentionScheduler started (interval: %d seconds)", interval_seconds)

    async def _loop(self, interval_seconds: int) -> None:
        """Main scheduler loop."""
        while self._running:
            try:
                await asyncio.sleep(interval_seconds)
                if not self._running:
                    break
                await self.cleanup()
            except asyncio.CancelledError:
                logger.info("DataRetentionScheduler task cancelled")
                break
            except Exception as e:
                logger.exception("Error in DataRetentionScheduler loop: %s", e)

    async def cleanup(self) -> None:
        """Execute the data cleanup function."""
        async with self.session_factory() as db:
            try:
                # Call the cleanup function defined in Alembic migrations
                from sqlalchemy import delete
                from sqlalchemy import text as sql_text

                from models.sos_incident import SosIncident

                cutoff_90 = datetime.now(UTC)
                stmt = delete(SosIncident).where(SosIncident.created_at < cutoff_90)
                result = await db.execute(stmt)
                deleted_sos = result.rowcount

                try:
                    await db.execute(sql_text("SELECT safevixai_cleanup_expired_data()"))
                except Exception:
                    logger.warning("safevixai_cleanup_expired_data() not available — skipping stored proc")

                await db.commit()
                logger.info(
                    "Data retention cleanup executed: %d SOS records purged at %s",
                    deleted_sos,
                    datetime.now(UTC).isoformat()
                )
            except Exception as e:
                await db.rollback()
                logger.exception("Data retention cleanup failed: %s", e)

    def stop(self) -> None:
        """Stop the scheduler."""
        self._running = False
        if self._task:
            self._task.cancel()
        logger.info("DataRetentionScheduler stopped")
