# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Background scheduler for periodic update checks."""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, AsyncSessionTransaction

from models.update_management import ReleaseChannel, UpdateSetting
from services.update_service import UpdateService

logger = logging.getLogger("safevixai.backend.update_scheduler")

SCHEDULE_MAP: dict[str, int] = {
    "immediate": 60,
    "hourly": 3600,
    "daily": 86400,
    "weekly": 604800,
}


class UpdateScheduler:
    """Periodic background scheduler for automated update checks.

    Runs at an interval determined by the schedule setting:
    - immediate: every 60 seconds
    - hourly: every 3600 seconds (1 hour)
    - daily: every 86400 seconds (24 hours, default)
    - weekly: every 604800 seconds (7 days)
    """

    def __init__(
        self,
        session_factory,
        update_service: Optional[UpdateService] = None,
    ) -> None:
        self._session_factory = session_factory
        self._service = update_service or UpdateService()
        self._task: Optional[asyncio.Task] = None
        self._running = False
        self._last_check: Optional[datetime] = None

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def last_check(self) -> Optional[datetime]:
        return self._last_check

    async def start(self) -> None:
        """Start the background scheduler loop."""
        if self._running:
            logger.warning("UpdateScheduler already running")
            return
        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info("UpdateScheduler started")

    async def stop(self) -> None:
        """Stop the background scheduler loop."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        logger.info("UpdateScheduler stopped")

    def _get_interval(self, schedule: str) -> int:
        return SCHEDULE_MAP.get(schedule, SCHEDULE_MAP["daily"])

    async def _run_loop(self) -> None:
        """Main scheduler loop."""
        while self._running:
            try:
                async with self._session_factory() as db:
                    settings = await self._get_settings(db)
                    interval = self._get_interval(settings.schedule)

                    if self._is_check_due(settings, interval):
                        logger.debug("Running scheduled update check (channel=%s)", settings.channel)
                        try:
                            result = await self._service.check_for_updates(db, settings.channel)
                            self._last_check = datetime.now(UTC)
                            if result.update_available:
                                logger.info(
                                    "Update available: v%s (mandatory=%s, security=%s)",
                                    result.latest_version, result.is_mandatory, result.is_security,
                                )
                            settings.last_check_result = (
                                result.latest_version if result.update_available else "up-to-date"
                            )
                            await db.commit()
                        except Exception as exc:
                            logger.warning("Scheduled update check failed: %s", exc)
                            settings.last_check_result = f"error: {exc}"
                            await db.commit()
            except Exception as exc:
                logger.error("UpdateScheduler loop error: %s", exc)

            interval = 3600  # default fallback
            try:
                async with self._session_factory() as db:
                    settings = await self._get_settings(db)
                    interval = self._get_interval(settings.schedule)
            except Exception:
                pass

            await asyncio.sleep(interval)

    def _is_check_due(self, settings: UpdateSetting, interval: int) -> bool:
        """Check if enough time has passed since the last check."""
        if not settings.last_checked_at:
            return True
        elapsed = (datetime.now(UTC) - settings.last_checked_at).total_seconds()
        return elapsed >= interval

    async def _get_settings(self, db: AsyncSession) -> UpdateSetting:
        stmt = select(UpdateSetting).limit(1)
        result = await db.execute(stmt)
        settings = result.scalar_one_or_none()
        if not settings:
            settings = UpdateSetting()
            db.add(settings)
            await db.commit()
            await db.refresh(settings)
        return settings

    async def get_status(self) -> dict:
        """Return scheduler status."""
        return {
            "running": self._running,
            "last_check": self._last_check.isoformat() if self._last_check else None,
            "task_active": self._task is not None and not self._task.done(),
        }
