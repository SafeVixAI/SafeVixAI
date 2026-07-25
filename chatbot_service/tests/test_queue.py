# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

import json
from unittest.mock import AsyncMock

import pytest

from core.queue import BackgroundWorker, TaskQueue, task


@task("test_chatbot_task")
async def dummy_chatbot_task_func(q, job_id, x):
    assert x == 99
    return "done"

@pytest.mark.asyncio
async def test_enqueue_chatbot_job():
    mock_redis = AsyncMock()
    mock_redis.hset = AsyncMock()
    mock_redis.rpush = AsyncMock()

    queue = TaskQueue(mock_redis)
    job_id = await queue.enqueue("test_chatbot_task", 99)

    assert job_id is not None
    assert mock_redis.hset.call_count == 1
    assert mock_redis.rpush.call_count == 1

    hset_args = mock_redis.hset.call_args[0]
    assert hset_args[0] == "svai:chatbot_jobs"
    assert hset_args[1] == job_id

    job_dict = json.loads(hset_args[2])
    assert job_dict["task_name"] == "test_chatbot_task"
    assert job_dict["args"] == [99]
    assert job_dict["status"] == "pending"


@pytest.mark.asyncio
async def test_chatbot_worker_processing():
    mock_redis = AsyncMock()
    mock_redis.hget = AsyncMock()
    mock_redis.hset = AsyncMock()

    job_id = "test-job-uuid-999"
    job_data = {
        "job_id": job_id,
        "task_name": "test_chatbot_task",
        "args": [99],
        "kwargs": {},
        "status": "pending",
        "retries_left": 3,
        "created_at": 12345.0,
    }

    mock_redis.hget.return_value = json.dumps(job_data)

    worker = BackgroundWorker(mock_redis, concurrency=1)
    await worker._process_job(job_id)

    assert mock_redis.hget.call_count == 1
    # hset called twice: once for "running", once for "success"
    assert mock_redis.hset.call_count == 2

    final_call_args = mock_redis.hset.call_args_list[-1][0]
    final_job_dict = json.loads(final_call_args[2])
    assert final_job_dict["status"] == "success"
    assert final_job_dict["result"] == "done"
    assert final_job_dict["error"] is None
