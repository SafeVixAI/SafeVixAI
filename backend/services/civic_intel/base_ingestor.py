# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Abstract base class for all civic intelligence ETL ingestors."""

from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import Any

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import get_settings
from models.etl_run_log import ETLRunLog

logger = logging.getLogger(__name__)


class BaseIngestor(ABC):
    """Enterprise ETL base — implements fetch → transform → load with audit logging.

    Subclasses implement:
        - name: str property — pipeline name for ETL log
        - fetch() — download raw data from external source
        - transform(raw) — normalize to list of dicts
        - load(db, records) — upsert into PostGIS tables
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Pipeline identifier used in etl_run_log."""
        ...

    @abstractmethod
    async def fetch(self) -> list[dict[str, Any]]:
        """Download raw data from external source. Returns raw records."""
        ...

    @abstractmethod
    async def transform(self, raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Normalize raw records to table-ready dicts."""
        ...

    @abstractmethod
    async def load(
        self, db: AsyncSession, records: list[dict[str, Any]],
    ) -> tuple[int, int, int]:
        """Upsert records into database. Returns (inserted, updated, skipped)."""
        ...

    async def run(self, db: AsyncSession) -> ETLRunLog:
        """Orchestrate the full ETL pipeline with audit logging."""
        settings = get_settings()
        log_entry = ETLRunLog(
            pipeline_name=self.name,
            started_at=datetime.now(UTC),
            status='running',
        )
        db.add(log_entry)
        await db.flush()

        t0 = time.monotonic()
        try:
            # Fetch
            logger.info('[ETL:%s] Fetching data...', self.name)
            raw = await self.fetch()
            log_entry.records_fetched = len(raw)
            logger.info('[ETL:%s] Fetched %d records', self.name, len(raw))

            # Transform
            records = await self.transform(raw)
            logger.info('[ETL:%s] Transformed to %d records', self.name, len(records))

            # Load in batches
            batch_size = settings.etl_batch_size
            total_inserted, total_updated, total_skipped = 0, 0, 0

            for i in range(0, len(records), batch_size):
                batch = records[i : i + batch_size]
                inserted, updated, skipped = await self.load(db, batch)
                total_inserted += inserted
                total_updated += updated
                total_skipped += skipped
                await db.commit()
                logger.info(
                    '[ETL:%s] Batch %d-%d: +%d ~%d -%d',
                    self.name, i, i + len(batch), inserted, updated, skipped,
                )

            log_entry.records_inserted = total_inserted
            log_entry.records_updated = total_updated
            log_entry.records_skipped = total_skipped
            log_entry.status = 'success'
            logger.info(
                '[ETL:%s] Completed: %d inserted, %d updated, %d skipped in %.1fs',
                self.name, total_inserted, total_updated, total_skipped,
                time.monotonic() - t0,
            )

        except Exception as exc:
            log_entry.status = 'failed'
            log_entry.error_message = f'{type(exc).__name__}: {exc}'
            logger.exception('[ETL:%s] Pipeline failed', self.name)

        finally:
            log_entry.finished_at = datetime.now(UTC)
            await db.commit()

        return log_entry

    def _get_http_client(self, **kwargs: Any) -> httpx.AsyncClient:
        """Create an httpx client with standard timeouts and user-agent."""
        settings = get_settings()
        return httpx.AsyncClient(
            timeout=httpx.Timeout(settings.request_timeout_seconds, connect=10.0),
            headers={'User-Agent': settings.http_user_agent},
            follow_redirects=True,
            **kwargs,
        )

    async def _fetch_with_retry(
        self, url: str, *, params: dict | None = None, max_retries: int = 3,
    ) -> httpx.Response:
        """Fetch URL with exponential backoff retry.

        Only retries on 5xx server errors and transport/network errors.
        4xx client errors (404, 403, etc.) are raised immediately — retrying
        a 404 endpoint wastes time and pollutes logs.
        """
        settings = get_settings()
        import asyncio

        last_exc: Exception | None = None
        for attempt in range(max_retries):
            try:
                async with self._get_http_client() as client:
                    resp = await client.get(url, params=params)
                    resp.raise_for_status()
                    return resp
            except httpx.HTTPStatusError as exc:
                # 4xx = client error — endpoint is gone/forbidden, don't retry
                if exc.response.status_code < 500:
                    raise
                last_exc = exc
                wait = settings.upstream_retry_backoff_seconds * (2 ** attempt)
                logger.warning(
                    '[ETL:%s] Retry %d/%d for %s: %s (wait %.1fs)',
                    self.name, attempt + 1, max_retries, url, exc, wait,
                )
                await asyncio.sleep(wait)
            except httpx.TransportError as exc:
                last_exc = exc
                wait = settings.upstream_retry_backoff_seconds * (2 ** attempt)
                logger.warning(
                    '[ETL:%s] Retry %d/%d for %s: %s (wait %.1fs)',
                    self.name, attempt + 1, max_retries, url, exc, wait,
                )
                await asyncio.sleep(wait)

        raise last_exc  # type: ignore[misc]
