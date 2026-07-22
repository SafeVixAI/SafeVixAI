# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI, Request

from core.cqrs import Command, CommandHandler, CQRSBus, Query, QueryHandler
from core.distributed_lock import Redlock, distributed_lock
from core.exception_handlers import (
    DomainError,
    InvalidTransitionError,
    ResourceNotFoundError,
    register_exception_handlers,
)
from core.redis_client import CacheHelper


@pytest.mark.asyncio
async def test_redlock_redis_success():
    cache = MagicMock(spec=CacheHelper)
    cache._client = AsyncMock()
    cache._client.set.return_value = True
    cache._client.eval.return_value = 1

    lock = Redlock("test_redis", ttl_seconds=10, cache=cache)
    acquired = await lock.acquire()
    assert acquired is True
    assert lock._has_lock is True

    await lock.release()
    assert lock._has_lock is False
    # Second release should be no-op
    await lock.release()


@pytest.mark.asyncio
async def test_redlock_redis_acquire_fails():
    cache = MagicMock(spec=CacheHelper)
    cache._client = AsyncMock()
    cache._client.set.return_value = False

    lock = Redlock("test_redis_fail", ttl_seconds=10, cache=cache)
    acquired = await lock.acquire()
    assert acquired is False
    assert lock._has_lock is False


@pytest.mark.asyncio
async def test_redlock_redis_exception_fallback():
    cache = MagicMock(spec=CacheHelper)
    cache._client = AsyncMock()
    cache._client.set.side_effect = Exception("Redis down")
    cache._client.eval.side_effect = Exception("Redis eval fail")

    lock = Redlock("test_redis_exc", ttl_seconds=10, cache=cache)
    acquired = await lock.acquire()
    assert acquired is True
    assert lock._has_lock is True

    await lock.release()
    assert lock._has_lock is False


@pytest.mark.asyncio
async def test_redlock_memory_timeout():
    cache = MagicMock(spec=CacheHelper)
    cache._client = None

    lock1 = Redlock("test_mem_timeout", ttl_seconds=10, cache=cache)
    assert await lock1.acquire() is True

    lock2 = Redlock("test_mem_timeout", ttl_seconds=10, cache=cache)
    assert await lock2.acquire() is False

    await lock1.release()


@pytest.mark.asyncio
async def test_distributed_lock_context_manager():
    cache = MagicMock(spec=CacheHelper)
    cache._client = None

    async with distributed_lock("test_cm", ttl_seconds=10, cache=cache) as acquired:
        assert acquired is True

    # Test when acquire fails
    lock1 = Redlock("test_cm_fail", ttl_seconds=10, cache=cache)
    await lock1.acquire()
    async with distributed_lock("test_cm_fail", ttl_seconds=10, cache=cache) as acquired:
        assert acquired is False
    await lock1.release()


@pytest.mark.asyncio
async def test_cqrs_bus():
    bus = CQRSBus()

    class SampleCommand(Command[str]):
        def __init__(self, val: str):
            self.val = val

    class SampleQuery(Query[str]):
        def __init__(self, val: str):
            self.val = val

    class SampleCommandHandler(CommandHandler[SampleCommand, str]):
        async def handle(self, command: SampleCommand) -> str:
            return f"CMD:{command.val}"

    class SampleQueryHandler(QueryHandler[SampleQuery, str]):
        async def handle(self, query: SampleQuery) -> str:
            return f"QRY:{query.val}"

    bus.register_command_handler(SampleCommand, SampleCommandHandler())
    bus.register_query_handler(SampleQuery, SampleQueryHandler())

    assert await bus.execute_command(SampleCommand("foo")) == "CMD:foo"
    assert await bus.execute_query(SampleQuery("bar")) == "QRY:bar"

    class UnregCommand(Command[str]):
        pass

    class UnregQuery(Query[str]):
        pass

    with pytest.raises(NotImplementedError):
        await bus.execute_command(UnregCommand())

    with pytest.raises(NotImplementedError):
        await bus.execute_query(UnregQuery())


@pytest.mark.asyncio
async def test_exception_handlers():
    app = FastAPI()
    register_exception_handlers(app)

    err = DomainError("Domain failed", status_code=400)
    assert err.message == "Domain failed"
    assert err.status_code == 400

    not_found = ResourceNotFoundError("Not found")
    assert not_found.status_code == 404

    trans_err = InvalidTransitionError("Transition invalid")
    assert trans_err.status_code == 409

    request = MagicMock(spec=Request)
    request.url.path = "/test"

    # Call handlers directly
    handlers = app.exception_handlers
    domain_handler = handlers.get(DomainError)
    res1 = await domain_handler(request, err)
    assert res1.status_code == 400

    from sqlalchemy.exc import IntegrityError
    integ_handler = handlers.get(IntegrityError)
    res2 = await integ_handler(request, IntegrityError("statement", "params", "orig"))
    assert res2.status_code == 409
