# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

import asyncio
import json
import logging
import uuid
import time
import sys
from pathlib import Path
from typing import Any, Callable, Optional

# Make sure project root is in path for alert_service
for parent in Path(__file__).resolve().parents:
    if (parent / 'alert_service.py').exists():
        if str(parent) not in sys.path:
            sys.path.insert(0, str(parent))
        break
from core.alert import get_alert_service

from redis.asyncio import Redis

logger = logging.getLogger("safevixai.chatbot.queue")

# Global registry of tasks
_TASK_REGISTRY: dict[str, Callable] = {}

def task(name: str):
    """Decorator to register a function as a background task."""
    def decorator(func: Callable):
        _TASK_REGISTRY[name] = func
        return func
    return decorator


class Job:
    def __init__(
        self,
        job_id: str,
        task_name: str,
        args: list[Any],
        kwargs: dict[str, Any],
        status: str = "pending",
        retries_left: int = 3,
        error: str | None = None,
        created_at: float | None = None,
        started_at: float | None = None,
        completed_at: float | None = None,
        progress: int = 0,
        result: Any | None = None,
    ):
        self.job_id = job_id
        self.task_name = task_name
        self.args = args
        self.kwargs = kwargs
        self.status = status
        self.retries_left = retries_left
        self.error = error
        self.created_at = created_at or time.time()
        self.started_at = started_at
        self.completed_at = completed_at
        self.progress = progress
        self.result = result

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "task_name": self.task_name,
            "args": self.args,
            "kwargs": self.kwargs,
            "status": self.status,
            "retries_left": self.retries_left,
            "error": self.error,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "progress": self.progress,
            "result": self.result,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Job:
        return cls(
            job_id=data["job_id"],
            task_name=data["task_name"],
            args=data["args"],
            kwargs=data["kwargs"],
            status=data["status"],
            retries_left=data["retries_left"],
            error=data.get("error"),
            created_at=data["created_at"],
            started_at=data.get("started_at"),
            completed_at=data.get("completed_at"),
            progress=data.get("progress", 0),
            result=data.get("result"),
        )


class TaskQueue:
    """Async Redis-backed Task Queue for Chatbot Service."""
    def __init__(self, redis_client: Redis, queue_name: str = "chatbot_default"):
        self.redis = redis_client
        self.queue_key = f"svai:queue:{queue_name}"
        
    async def enqueue(self, task_name: str, *args, retries: int = 3, **kwargs) -> str:
        if task_name not in _TASK_REGISTRY:
            logger.warning("Enqueueing unregistered chatbot task: %s", task_name)
            
        job_id = str(uuid.uuid4())
        job = Job(
            job_id=job_id,
            task_name=task_name,
            args=list(args),
            kwargs=kwargs,
            retries_left=retries,
        )
        
        await self.redis.hset("svai:chatbot_jobs", job_id, json.dumps(job.to_dict()))
        await self.redis.rpush(self.queue_key, job_id)
        logger.info("Enqueued chatbot background job: %s (task: %s)", job_id, task_name)
        return job_id

    async def get_job(self, job_id: str) -> Optional[Job]:
        raw = await self.redis.hget("svai:chatbot_jobs", job_id)
        if not raw:
            return None
        return Job.from_dict(json.loads(raw))

    async def update_progress(self, job_id: str, progress: int, status: str = "running", result: Any | None = None):
        job = await self.get_job(job_id)
        if job:
            job.progress = progress
            job.status = status
            if result is not None:
                job.result = result
            await self.redis.hset("svai:chatbot_jobs", job_id, json.dumps(job.to_dict()))


class BackgroundWorker:
    """Worker loop that runs in the background of our FastAPI app context."""
    def __init__(self, redis_client: Redis, queue_name: str = "chatbot_default", concurrency: int = 1):
        self.redis = redis_client
        self.queue_key = f"svai:queue:{queue_name}"
        self.concurrency = concurrency
        self.running = False
        self._tasks: list[asyncio.Task] = []

    async def start(self):
        self.running = True
        for i in range(self.concurrency):
            t = asyncio.create_task(self._worker_loop(i))
            self._tasks.append(t)
        logger.info("Started %d async chatbot background worker loops", self.concurrency)

    async def stop(self):
        self.running = False
        for t in self._tasks:
            t.cancel()
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()
        logger.info("Stopped chatbot background worker loops")

    async def _worker_loop(self, worker_id: int):
        while self.running:
            try:
                res = await self.redis.blpop(self.queue_key, timeout=2)
                if not res:
                    continue
                    
                _, job_id = res
                await self._process_job(job_id)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception("Chatbot worker error on loop %d: %s", worker_id, e)
                await asyncio.sleep(1)

    async def _process_job(self, job_id: str):
        raw = await self.redis.hget("svai:chatbot_jobs", job_id)
        if not raw:
            logger.error("Chatbot job %s not found in status store", job_id)
            return

        job_dict = json.loads(raw)
        job = Job.from_dict(job_dict)
        
        job.status = "running"
        job.started_at = time.time()
        await self.redis.hset("svai:chatbot_jobs", job_id, json.dumps(job.to_dict()))
        
        func = _TASK_REGISTRY.get(job.task_name)
        if not func:
            err_msg = f"Task function for '{job.task_name}' is not registered."
            logger.error(err_msg)
            job.status = "failed"
            job.error = err_msg
            job.completed_at = time.time()
            await self.redis.hset("svai:chatbot_jobs", job_id, json.dumps(job.to_dict()))
            return

        logger.info("Processing chatbot job %s (task: %s)", job_id, job.task_name)
        try:
            # Pass task queue instance for progress reporting if required
            q = TaskQueue(self.redis)
            if asyncio.iscoroutinefunction(func):
                res = await func(q, job_id, *job.args, **job.kwargs)
            else:
                res = func(q, job_id, *job.args, **job.kwargs)
                
            job.status = "success"
            job.progress = 100
            job.result = res
            logger.info("Chatbot job %s completed successfully", job_id)
        except Exception as exc:
            logger.exception("Chatbot job %s failed: %s", job_id, exc)
            job.retries_left -= 1
            if job.retries_left >= 0:
                logger.info("Re-queueing chatbot job %s, retries left: %d", job_id, job.retries_left)
                job.status = "pending"
                await self.redis.hset("svai:chatbot_jobs", job_id, json.dumps(job.to_dict()))
                await asyncio.sleep(2 ** (3 - job.retries_left))
                await self.redis.rpush(self.queue_key, job_id)
                return
            else:
                job.status = "failed"
                job.error = str(exc)
                logger.error("Chatbot job %s permanently failed. Sending alert.", job_id)
                
                get_alert_service().alert_external_api_failed(
                    service_name=f"Chatbot Background Job: {job.task_name}",
                    endpoint="Queue worker",
                    status_code=500,
                    error_msg=f"Chatbot job {job_id} permanently failed after retries: {str(exc)}"
                )
                
        job.completed_at = time.time()
        await self.redis.hset("svai:chatbot_jobs", job_id, json.dumps(job.to_dict()))


_chat_engine: Any = None

def set_global_chat_engine(engine: Any):
    global _chat_engine
    _chat_engine = engine

def get_global_chat_engine() -> Any:
    return _chat_engine

