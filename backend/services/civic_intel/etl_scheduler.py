# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""ETL Scheduler — asyncio background loop for all civic intelligence pipelines."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select, desc

from core.config import get_settings
from models.etl_run_log import ETLRunLog
from services.civic_intel.lgd_ingestor import LGDIngestor
from services.civic_intel.boundary_ingestor import BoundaryIngestor
from services.civic_intel.osm_bulk_ingestor import OSMBulkIngestor
from services.civic_intel.datagov_ingestor import DataGovIngestor
from services.civic_intel.municipal_ingestor import MunicipalIngestor
from services.civic_intel.grievance_ingestor import GrievanceIngestor

logger = logging.getLogger(__name__)


class ETLScheduler:
    """Background scheduler for civic intelligence ETL pipelines.

    Same pattern as the existing SLAMonitor — asyncio loop with configurable
    intervals per pipeline. Runs inside the FastAPI lifespan.
    """

    SCHEDULES: dict[str, timedelta] = {
        'lgd': timedelta(days=7),
        'boundaries': timedelta(days=30),
        'osm_civic': timedelta(days=7),
        'datagov': timedelta(days=30),
        'municipal': timedelta(days=1),
        'grievance': timedelta(days=1),
    }

    def __init__(self, session_factory: Any, overpass_service: Any = None):
        self._session_factory = session_factory
        self._overpass_service = overpass_service
        self._running = False
        self._task: asyncio.Task | None = None
        self._ingestors = {
            'lgd': LGDIngestor(),
            'boundaries': BoundaryIngestor(),
            'osm_civic': OSMBulkIngestor(overpass_service=overpass_service),
            'datagov': DataGovIngestor(),
            'municipal': MunicipalIngestor(),
            'grievance': GrievanceIngestor(),
        }

    async def start(self) -> None:
        """Start the background ETL loop."""
        settings = get_settings()
        if not settings.etl_enabled:
            logger.info('[ETLScheduler] ETL disabled via ETL_ENABLED=false')
            return

        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info('[ETLScheduler] Started background ETL scheduler')

    async def stop(self) -> None:
        """Stop the background ETL loop."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                logger.info("ETL scheduler task cancelled — graceful stop")
        logger.info('[ETLScheduler] Stopped')

    async def _run_loop(self, check_interval: int = 3600) -> None:
        """Main scheduler loop — checks every hour which pipelines need to run."""
        while self._running:
            try:
                for pipeline_name, interval in self.SCHEDULES.items():
                    try:
                        should_run = await self._should_run(pipeline_name, interval)
                        if should_run:
                            logger.info('[ETLScheduler] Running pipeline: %s', pipeline_name)
                            await self.run_pipeline(pipeline_name)
                    except Exception as exc:
                        logger.error('[ETLScheduler] %s check failed: %s', pipeline_name, exc)

            except Exception as exc:
                logger.error('[ETLScheduler] Loop error: %s', exc)

            await asyncio.sleep(check_interval)

    async def _should_run(self, pipeline_name: str, interval: timedelta) -> bool:
        """Check if a pipeline needs to run based on last successful run."""
        async with self._session_factory() as db:
            result = await db.execute(
                select(ETLRunLog)
                .where(ETLRunLog.pipeline_name == pipeline_name)
                .where(ETLRunLog.status.in_(['success', 'partial']))
                .order_by(desc(ETLRunLog.started_at))
                .limit(1)
            )
            last_run = result.scalar_one_or_none()

            if last_run is None:
                return True  # Never run before

            now = datetime.now(timezone.utc)
            last_time = last_run.started_at
            if last_time.tzinfo is None:
                last_time = last_time.replace(tzinfo=timezone.utc)

            return (now - last_time) > interval

    async def run_pipeline(self, pipeline_name: str) -> ETLRunLog | None:
        """Manually trigger a specific pipeline."""
        ingestor = self._ingestors.get(pipeline_name)
        if not ingestor:
            logger.error('[ETLScheduler] Unknown pipeline: %s', pipeline_name)
            return None

        async with self._session_factory() as db:
            try:
                result = await ingestor.run(db)
                logger.info(
                    '[ETLScheduler] %s completed: status=%s, inserted=%d',
                    pipeline_name, result.status, result.records_inserted,
                )
                return result
            except Exception as exc:
                logger.exception('[ETLScheduler] %s failed: %s', pipeline_name, exc)
                return None

    async def get_status(self) -> dict[str, Any]:
        """Get status of all pipelines."""
        status: dict[str, Any] = {}
        async with self._session_factory() as db:
            for pipeline_name in self.SCHEDULES:
                result = await db.execute(
                    select(ETLRunLog)
                    .where(ETLRunLog.pipeline_name == pipeline_name)
                    .order_by(desc(ETLRunLog.started_at))
                    .limit(1)
                )
                last_run = result.scalar_one_or_none()
                status[pipeline_name] = {
                    'last_run': last_run.started_at.isoformat() if last_run else None,
                    'status': last_run.status if last_run else 'never_run',
                    'records': last_run.records_inserted if last_run else 0,
                }
        return status
