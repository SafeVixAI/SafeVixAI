# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

import asyncio
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from core.queue import TaskQueue, BackgroundWorker, _TASK_REGISTRY


@pytest.fixture(autouse=True)
def cleanup_registry():
    """Remove any test-specific tasks after each test."""
    yield
    for name in list(_TASK_REGISTRY.keys()):
        if name.startswith("_test_"):
            del _TASK_REGISTRY[name]


# ── BackgroundWorker lifecycle ────────────────────────────────────────────────

class TestBackgroundWorkerLifecycle:
    @pytest.mark.asyncio
    async def test_start_creates_tasks_and_sets_running(self):
        mock_redis = AsyncMock()
        worker = BackgroundWorker(mock_redis, concurrency=2)

        assert not worker.running
        assert len(worker._tasks) == 0

        await worker.start()

        assert worker.running is True
        assert len(worker._tasks) == 2
        for t in worker._tasks:
            assert not t.done()

        await worker.stop()

    @pytest.mark.asyncio
    async def test_stop_cancels_tasks_and_clears(self):
        mock_redis = AsyncMock()
        worker = BackgroundWorker(mock_redis, concurrency=1)

        await worker.start()
        assert len(worker._tasks) == 1

        await worker.stop()

        assert worker.running is False
        assert len(worker._tasks) == 0

    @pytest.mark.asyncio
    async def test_stop_does_not_crash_when_not_started(self):
        mock_redis = AsyncMock()
        worker = BackgroundWorker(mock_redis)

        await worker.stop()
        assert worker.running is False


# ── _process_job retry logic ──────────────────────────────────────────────────

def _register_failing_task(task_name="_test_fail_task"):
    """Register a task that always raises ValueError."""
    async def _fail_fn():
        raise ValueError("Simulated failure")
    _TASK_REGISTRY[task_name] = _fail_fn
    return task_name


class TestProcessJobRetry:
    @pytest.mark.asyncio
    async def test_retries_decremented_and_requeued(self):
        """When retries_left > 0, job is re-queued with decremented counter."""
        task_name = _register_failing_task("_test_retry_task")
        mock_redis = AsyncMock()
        job_id = "retry-job-uuid"
        job_dict = {
            "job_id": job_id,
            "task_name": task_name,
            "args": [],
            "kwargs": {},
            "status": "pending",
            "retries_left": 1,
            "created_at": 12345.0,
        }
        mock_redis.hget.return_value = json.dumps(job_dict)
        mock_redis.hset = AsyncMock()
        mock_redis.blpop = AsyncMock()
        mock_redis.rpush = AsyncMock()

        worker = BackgroundWorker(mock_redis)

        with patch("asyncio.sleep", AsyncMock()):
            await worker._process_job(job_id)

        all_sets = [args[0][2] for args in mock_redis.hset.call_args_list]
        final_state = None
        for raw in all_sets:
            d = json.loads(raw)
            if d["status"] == "pending":
                final_state = d
        assert final_state is not None
        assert final_state["retries_left"] == 0
        assert final_state["status"] == "pending"
        assert mock_redis.rpush.call_count == 1

    @pytest.mark.asyncio
    async def test_retries_exhausted_fails_and_alerts(self):
        """When retries_left is 0 and job fails, alert is sent."""
        task_name = _register_failing_task("_test_exhausted_task")
        mock_redis = AsyncMock()
        job_id = "exhausted-job-uuid"
        job_dict = {
            "job_id": job_id,
            "task_name": task_name,
            "args": [],
            "kwargs": {},
            "status": "pending",
            "retries_left": 0,
            "created_at": 12345.0,
        }
        mock_redis.hget.return_value = json.dumps(job_dict)
        mock_redis.hset = AsyncMock()

        mock_alert = MagicMock()
        mock_alert.alert_external_api_failed = MagicMock()
        worker = BackgroundWorker(mock_redis)

        with patch("core.queue.get_alert_service", return_value=mock_alert):
            await worker._process_job(job_id)

        all_sets = [json.loads(args[0][2]) for args in mock_redis.hset.call_args_list]
        failed_state = None
        for d in all_sets:
            if d["status"] == "failed":
                failed_state = d
        assert failed_state is not None
        assert failed_state["status"] == "failed"
        assert "Simulated failure" in failed_state["error"]

        mock_alert.alert_external_api_failed.assert_called_once()
        call_args = mock_alert.alert_external_api_failed.call_args[1]
        assert "Background Job" in call_args["service_name"]

    @pytest.mark.asyncio
    async def test_unregistered_task_fails_immediately(self):
        """Job with unregistered task name fails without retrying."""
        mock_redis = AsyncMock()
        job_id = "unreg-job-uuid"
        job_dict = {
            "job_id": job_id,
            "task_name": "_test_nonexistent_task",
            "args": [],
            "kwargs": {},
            "status": "pending",
            "retries_left": 3,
            "created_at": 12345.0,
        }
        mock_redis.hget.return_value = json.dumps(job_dict)
        mock_redis.hset = AsyncMock()

        worker = BackgroundWorker(mock_redis)
        await worker._process_job(job_id)

        all_sets = [json.loads(args[0][2]) for args in mock_redis.hset.call_args_list]
        failed_state = None
        for d in all_sets:
            if d["status"] == "failed":
                failed_state = d
        assert failed_state is not None
        assert "not registered" in failed_state["error"].lower()

    @pytest.mark.asyncio
    async def test_sync_task_func_is_supported(self):
        """_process_job handles synchronous task functions."""
        call_flag = {}

        def _sync_fn():
            call_flag["called"] = True
        _TASK_REGISTRY["_test_sync_task"] = _sync_fn

        mock_redis = AsyncMock()
        job_id = "sync-job-uuid"
        job_dict = {
            "job_id": job_id,
            "task_name": "_test_sync_task",
            "args": [],
            "kwargs": {},
            "status": "pending",
            "retries_left": 3,
            "created_at": 12345.0,
        }
        mock_redis.hget.return_value = json.dumps(job_dict)
        mock_redis.hset = AsyncMock()

        worker = BackgroundWorker(mock_redis)
        await worker._process_job(job_id)

        assert call_flag.get("called") is True
        all_sets = [json.loads(args[0][2]) for args in mock_redis.hset.call_args_list]
        success_state = None
        for d in all_sets:
            if d["status"] == "success":
                success_state = d
        assert success_state is not None

    @pytest.mark.asyncio
    async def test_job_not_found_logs_and_returns(self):
        """When job is not in redis, _process_job returns early."""
        mock_redis = AsyncMock()
        mock_redis.hget.return_value = None

        worker = BackgroundWorker(mock_redis)
        await worker._process_job("nonexistent-job")

        mock_redis.hset.assert_not_called()


# ── enqueue / get_job with mock Redis ────────────────────────────────────────

class TestTaskQueue:
    @pytest.mark.asyncio
    async def test_enqueue_unregistered_task_logs_warning(self):
        mock_redis = AsyncMock()
        mock_redis.rpush = AsyncMock()
        mock_redis.hset = AsyncMock()

        queue = TaskQueue(mock_redis)
        job_id = await queue.enqueue("_test_unknown_task", 99)

        assert job_id is not None
        assert mock_redis.hset.call_count == 1
        assert mock_redis.rpush.call_count == 1

    @pytest.mark.asyncio
    async def test_get_job_returns_none_for_missing(self):
        mock_redis = AsyncMock()
        mock_redis.hget.return_value = None

        queue = TaskQueue(mock_redis)
        job = await queue.get_job("missing-id")
        assert job is None

    @pytest.mark.asyncio
    async def test_get_job_returns_parsed_job(self):
        job_data = {
            "job_id": "uuid-123",
            "task_name": "test_task",
            "args": [1, 2],
            "kwargs": {"key": "val"},
            "status": "running",
            "retries_left": 2,
            "error": None,
            "created_at": 100.0,
            "started_at": 101.0,
            "completed_at": 102.0,
        }
        mock_redis = AsyncMock()
        mock_redis.hget.return_value = json.dumps(job_data)

        queue = TaskQueue(mock_redis)
        job = await queue.get_job("uuid-123")

        assert job is not None
        assert job.job_id == "uuid-123"
        assert job.task_name == "test_task"
        assert job.args == [1, 2]
        assert job.kwargs == {"key": "val"}
        assert job.status == "running"
        assert job.retries_left == 2
        assert job.started_at == 101.0
        assert job.completed_at == 102.0

    @pytest.mark.asyncio
    async def test_enqueue_stores_correct_initial_state(self):
        mock_redis = AsyncMock()
        mock_redis.rpush = AsyncMock()
        mock_redis.hset = AsyncMock()

        queue = TaskQueue(mock_redis)
        job_id = await queue.enqueue("_test_job", "arg1", retries=5, kw="val")

        hset_args = mock_redis.hset.call_args[0]
        stored = json.loads(hset_args[2])
        assert stored["task_name"] == "_test_job"
        assert stored["args"] == ["arg1"]
        assert stored["kwargs"] == {"kw": "val"}
        assert stored["status"] == "pending"
        assert stored["retries_left"] == 5
        assert stored["job_id"] == job_id


# ── _worker_loop exception handling ───────────────────────────────────────────

class TestWorkerLoop:
    @pytest.mark.asyncio
    async def test_worker_loop_cancelled_error_breaks(self):
        """_worker_loop handles CancelledError and breaks out of the loop."""
        mock_redis = AsyncMock()
        mock_redis.blpop = AsyncMock(side_effect=asyncio.CancelledError())
        worker = BackgroundWorker(mock_redis)
        worker.running = True
        with patch("core.queue.asyncio.sleep", AsyncMock()) as mock_sleep:
            await worker._worker_loop(0)
        mock_sleep.assert_not_called()

    @pytest.mark.asyncio
    async def test_worker_loop_processes_job_when_blpop_returns_data(self):
        """When blpop returns data, _worker_loop processes the job (covers lines 155-156)."""
        mock_redis = AsyncMock()
        mock_redis.blpop = AsyncMock(side_effect=[
            (b"queue", b"job-abc"),
            asyncio.CancelledError(),
        ])
        worker = BackgroundWorker(mock_redis)
        worker.running = True
        with patch.object(worker, '_process_job', AsyncMock()) as mock_process:
            with patch("core.queue.asyncio.sleep", AsyncMock()):
                await worker._worker_loop(0)
        mock_process.assert_awaited_once_with(b"job-abc")

    @pytest.mark.asyncio
    async def test_worker_loop_blpop_none_continues(self):
        """When blpop returns None (timeout), _worker_loop continues to next iteration."""
        mock_redis = AsyncMock()
        mock_redis.blpop = AsyncMock(side_effect=[None, asyncio.CancelledError()])
        worker = BackgroundWorker(mock_redis)
        worker.running = True
        with patch("core.queue.asyncio.sleep", AsyncMock()) as mock_sleep:
            await worker._worker_loop(0)
        mock_sleep.assert_not_called()

    @pytest.mark.asyncio
    async def test_worker_loop_general_exception_caught(self):
        """_worker_loop catches generic exceptions, sleeps, and continues."""
        mock_redis = AsyncMock()
        mock_redis.blpop = AsyncMock(side_effect=ValueError("test-error"))
        worker = BackgroundWorker(mock_redis)
        worker.running = True
        async def _stop(duration):
            worker.running = False
        with patch("core.queue.asyncio.sleep", _stop):
            with patch("core.queue.logger.exception") as mock_log:
                await worker._worker_loop(0)
        mock_log.assert_called_once()
        assert "test-error" in str(mock_log.call_args[0][2])


# ── enqueue with registered task ──────────────────────────────────────────────

class TestEnqueueRegistered:
    @pytest.mark.asyncio
    async def test_enqueue_registered_task_skips_warning(self):
        """Enqueueing a registered task does not hit the unregistered warning path (branch 99->102)."""
        async def _dummy():
            pass
        _TASK_REGISTRY["_test_registered_enqueue"] = _dummy
        mock_redis = AsyncMock()
        mock_redis.rpush = AsyncMock()
        mock_redis.hset = AsyncMock()
        queue = TaskQueue(mock_redis)
        job_id = await queue.enqueue("_test_registered_enqueue", 42)
        assert job_id is not None
        stored = json.loads(mock_redis.hset.call_args[0][2])
        assert stored["task_name"] == "_test_registered_enqueue"
        assert stored["args"] == [42]
