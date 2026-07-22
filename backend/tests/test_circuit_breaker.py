# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

import time

import pytest

from core.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerOpenError,
    CircuitBreakerRegistry,
    CircuitState,
)


class TestCircuitBreaker:
    def test_init_defaults(self):
        cb = CircuitBreaker(name="test")
        assert cb.name == "test"
        assert cb.state == CircuitState.CLOSED
        assert cb.state_name == "closed"

    def test_init_custom(self):
        cb = CircuitBreaker(
            name="test",
            failure_threshold=3,
            recovery_timeout=10.0,
            half_open_max_requests=2,
            success_threshold=1,
        )
        assert cb._failure_threshold == 3
        assert cb._recovery_timeout == 10.0
        assert cb._half_open_max_requests == 2
        assert cb._success_threshold == 1

    @pytest.mark.asyncio
    async def test_successful_call(self):
        cb = CircuitBreaker(name="test")

        async def success():
            return "ok"

        result = await cb.call(success)
        assert result == "ok"
        assert cb.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_failure_opens_circuit(self):
        cb = CircuitBreaker(name="test", failure_threshold=2)

        async def fail():
            raise ValueError("oops")

        with pytest.raises(ValueError):
            await cb.call(fail)
        assert cb.state == CircuitState.CLOSED

        with pytest.raises(ValueError):
            await cb.call(fail)
        assert cb.state == CircuitState.OPEN

    @pytest.mark.asyncio
    async def test_open_circuit_rejects(self):
        cb = CircuitBreaker(name="test", failure_threshold=1, recovery_timeout=60.0)

        async def fail():
            raise ValueError("oops")

        with pytest.raises(ValueError):
            await cb.call(fail)
        assert cb.state == CircuitState.OPEN

        with pytest.raises(CircuitBreakerOpenError):
            await cb.call(fail)

    @pytest.mark.asyncio
    async def test_recovery_timeout_transitions_to_half_open(self):
        cb = CircuitBreaker(name="test", failure_threshold=1, recovery_timeout=0.05)

        async def fail():
            raise ValueError("oops")

        with pytest.raises(ValueError):
            await cb.call(fail)
        assert cb.state == CircuitState.OPEN

        time.sleep(0.06)

        async def success():
            return "recovered"

        result = await cb.call(success)
        assert result == "recovered"
        assert cb.state == CircuitState.HALF_OPEN

    @pytest.mark.asyncio
    async def test_half_open_success_closes_circuit(self):
        cb = CircuitBreaker(name="test", failure_threshold=1, recovery_timeout=0.05, success_threshold=1)

        async def fail():
            raise ValueError("oops")

        with pytest.raises(ValueError):
            await cb.call(fail)

        time.sleep(0.06)

        async def success():
            return "ok"

        result = await cb.call(success)
        assert result == "ok"
        assert cb.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_half_open_failure_reopens(self):
        cb = CircuitBreaker(name="test", failure_threshold=1, recovery_timeout=0.05)

        async def fail():
            raise ValueError("oops")

        with pytest.raises(ValueError):
            await cb.call(fail)

        time.sleep(0.06)

        async def still_fail():
            raise RuntimeError("still failing")

        with pytest.raises(RuntimeError):
            await cb.call(still_fail)
        assert cb.state == CircuitState.OPEN

    @pytest.mark.asyncio
    async def test_sync_function_call(self):
        cb = CircuitBreaker(name="test")

        def sync_success():
            return "sync"

        result = await cb.call(sync_success)
        assert result == "sync"

    def test_get_stats(self):
        cb = CircuitBreaker(name="test")
        stats = cb.get_stats()
        assert stats["name"] == "test"
        assert stats["state"] == "closed"
        assert stats["total_calls"] == 0
        assert "failure_threshold" in stats
        assert "recovery_timeout" in stats

    def test_stats_after_failures(self):
        cb = CircuitBreaker(name="test", failure_threshold=3)
        cb._on_failure(ValueError("fail 1"))
        cb._on_failure(ValueError("fail 2"))
        cb._on_failure(ValueError("fail 3"))

        stats = cb.get_stats()
        assert stats["total_failures"] == 3
        assert stats["state"] == "open"


class TestCircuitBreakerRegistry:
    def test_get_or_create(self):
        cb1 = CircuitBreakerRegistry.get("service-a")
        cb2 = CircuitBreakerRegistry.get("service-a")
        assert cb1 is cb2

    def test_multiple_breakers(self):
        cb1 = CircuitBreakerRegistry.get("service-a")
        cb2 = CircuitBreakerRegistry.get("service-b")
        assert cb1 is not cb2

    def test_all_stats(self):
        CircuitBreakerRegistry.reset_all()
        CircuitBreakerRegistry.get("svc-a")
        CircuitBreakerRegistry.get("svc-b")
        stats = CircuitBreakerRegistry.all_stats()
        assert "svc-a" in stats
        assert "svc-b" in stats

    def test_reset_all(self):
        CircuitBreakerRegistry.get("svc-a")
        CircuitBreakerRegistry.reset_all()
        assert CircuitBreakerRegistry.all_stats() == {}

    def test_custom_params(self):
        CircuitBreakerRegistry.reset_all()
        cb = CircuitBreakerRegistry.get("custom", failure_threshold=3, recovery_timeout=15.0)
        assert cb._failure_threshold == 3
        assert cb._recovery_timeout == 15.0
