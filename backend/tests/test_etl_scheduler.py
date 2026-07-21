# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.civic_intel.etl_scheduler import ETLScheduler


def _mock_session_factory():
    db = AsyncMock()
    db.__aenter__ = AsyncMock(return_value=db)
    db.__aexit__ = AsyncMock(return_value=None)
    db.execute = AsyncMock()
    return db


def _mock_result(row=None):
    """Return a MagicMock that mimics a DB result with scalar_one_or_none."""
    r = MagicMock()
    r.scalar_one_or_none.return_value = row
    return r


def _mock_etl_run_log(pipeline_name, status="success", records=10, age_hours=0):
    log = MagicMock()
    log.pipeline_name = pipeline_name
    log.status = status
    log.records_inserted = records
    log.started_at = datetime.now(timezone.utc) - timedelta(hours=age_hours)
    return log


class TestETLSchedulerInit:

    def test_schedules_defined(self):
        scheduler = ETLScheduler(None)
        assert set(scheduler.SCHEDULES.keys()) == {
            "lgd", "boundaries", "osm_civic", "datagov", "municipal", "grievance"
        }

    def test_ingestors_created(self):
        scheduler = ETLScheduler(None)
        assert set(scheduler._ingestors.keys()) == {
            "lgd", "boundaries", "osm_civic", "datagov", "municipal", "grievance"
        }

    def test_not_running_initially(self):
        scheduler = ETLScheduler(None)
        assert scheduler._running is False
        assert scheduler._task is None


class TestETLSchedulerStart:

    @pytest.mark.asyncio
    async def test_start_with_etl_enabled(self):
        scheduler = ETLScheduler(None)
        with patch("services.civic_intel.etl_scheduler.get_settings") as mock_settings:
            settings = MagicMock()
            settings.etl_enabled = True
            mock_settings.return_value = settings
            await scheduler.start()
        assert scheduler._running is True
        assert scheduler._task is not None
        await scheduler.stop()

    @pytest.mark.asyncio
    async def test_start_with_etl_disabled(self):
        scheduler = ETLScheduler(None)
        with patch("services.civic_intel.etl_scheduler.get_settings") as mock_settings:
            settings = MagicMock()
            settings.etl_enabled = False
            mock_settings.return_value = settings
            await scheduler.start()
        assert scheduler._running is False
        assert scheduler._task is None


class TestETLSchedulerStop:

    @pytest.mark.asyncio
    async def test_stop_cancels_task(self):
        scheduler = ETLScheduler(None)
        scheduler._running = True
        scheduler._task = asyncio.create_task(asyncio.sleep(999))
        await scheduler.stop()
        assert scheduler._running is False
        assert scheduler._task.cancelled()

    @pytest.mark.asyncio
    async def test_stop_without_task(self):
        scheduler = ETLScheduler(None)
        await scheduler.stop()
        assert scheduler._running is False


class TestETLSchedulerShouldRun:

    @pytest.mark.asyncio
    async def test_no_previous_run_returns_true(self):
        db = _mock_session_factory()
        db.execute.return_value = _mock_result(row=None)
        scheduler = ETLScheduler(lambda: db)
        result = await scheduler._should_run("lgd", timedelta(days=7))
        assert result is True

    @pytest.mark.asyncio
    async def test_recent_run_within_interval_returns_false(self):
        log = _mock_etl_run_log("lgd", age_hours=1)
        db = _mock_session_factory()
        db.execute.return_value = _mock_result(row=log)
        scheduler = ETLScheduler(lambda: db)
        result = await scheduler._should_run("lgd", timedelta(days=7))
        assert result is False

    @pytest.mark.asyncio
    async def test_old_run_past_interval_returns_true(self):
        log = _mock_etl_run_log("lgd", age_hours=200)
        db = _mock_session_factory()
        db.execute.return_value = _mock_result(row=log)
        scheduler = ETLScheduler(lambda: db)
        result = await scheduler._should_run("lgd", timedelta(days=7))
        assert result is True

    @pytest.mark.asyncio
    async def test_naive_datetime_normalized(self):
        log = MagicMock()
        log.started_at = datetime.now() - timedelta(days=30)
        db = _mock_session_factory()
        db.execute.return_value = _mock_result(row=log)
        scheduler = ETLScheduler(lambda: db)
        result = await scheduler._should_run("lgd", timedelta(days=7))
        assert result is True


class TestETLSchedulerRunPipeline:

    @pytest.mark.asyncio
    async def test_known_pipeline_calls_ingestor(self):
        mock_ingestor = AsyncMock()
        mock_ingestor.run.return_value = _mock_etl_run_log("lgd")
        db = _mock_session_factory()
        scheduler = ETLScheduler(lambda: db)
        scheduler._ingestors = {"lgd": mock_ingestor}
        result = await scheduler.run_pipeline("lgd")
        assert result is not None
        assert result.pipeline_name == "lgd"
        mock_ingestor.run.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_unknown_pipeline_returns_none(self):
        scheduler = ETLScheduler(None)
        result = await scheduler.run_pipeline("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_ingestor_exception_returns_none(self):
        mock_ingestor = AsyncMock()
        mock_ingestor.run.side_effect = RuntimeError("Ingestor crashed")
        db = _mock_session_factory()
        scheduler = ETLScheduler(lambda: db)
        scheduler._ingestors = {"lgd": mock_ingestor}
        result = await scheduler.run_pipeline("lgd")
        assert result is None


class TestETLSchedulerGetStatus:

    @pytest.mark.asyncio
    async def test_returns_status_for_all_pipelines(self):
        log = _mock_etl_run_log("lgd", age_hours=1)
        db = _mock_session_factory()

        call_count = 0

        def execute_side_effect(*args):
            nonlocal call_count
            r = MagicMock()
            # First call is for "lgd" pipeline
            r.scalar_one_or_none.return_value = log if call_count == 0 else None
            call_count += 1
            return r

        db.execute.side_effect = execute_side_effect
        scheduler = ETLScheduler(lambda: db)
        status = await scheduler.get_status()
        assert "lgd" in status
        assert status["lgd"]["last_run"] is not None
        assert status["lgd"]["status"] == "success"
        assert status["lgd"]["records"] == 10

    @pytest.mark.asyncio
    async def test_never_run_shows_never_run(self):
        db = _mock_session_factory()
        db.execute.return_value = _mock_result(row=None)
        scheduler = ETLScheduler(lambda: db)
        status = await scheduler.get_status()
        for pipeline_name in scheduler.SCHEDULES:
            assert status[pipeline_name]["status"] == "never_run"
            assert status[pipeline_name]["last_run"] is None
            assert status[pipeline_name]["records"] == 0


class TestETLSchedulerRunLoop:

    @pytest.mark.asyncio
    async def test_loop_runs_pipelines(self):
        scheduler = ETLScheduler(None)
        scheduler._running = True

        async def mock_should_run(*args):
            return True

        async def mock_run_pipeline(*args):
            return _mock_etl_run_log(args[0])

        scheduler._should_run = mock_should_run
        scheduler.run_pipeline = mock_run_pipeline
        scheduler.SCHEDULES = {"lgd": timedelta(days=7)}

        task = asyncio.create_task(scheduler._run_loop(check_interval=0.01))
        await asyncio.sleep(0.03)
        scheduler._running = False
        task.cancel()
        try:
            await task
        except (asyncio.CancelledError, RuntimeError):
            pass
