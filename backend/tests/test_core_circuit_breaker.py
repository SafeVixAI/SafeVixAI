# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Core circuit breaker tests — transitions, force methods, edge cases, registry."""
from __future__ import annotations

import time

import pytest

from core.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerOpenError,
    CircuitBreakerRegistry,
    CircuitState,
)


class TestCoreCircuitBreakerState:
    """Tests for initial state and property accessors."""

    def test_initial_state_closed(self):
        cb = CircuitBreaker(name="test")
        assert cb.state == CircuitState.CLOSED
        assert cb.state_name == "closed"

    def test_force_open_transitions(self):
        cb = CircuitBreaker(name="test")
        cb.force_open()
        assert cb.state == CircuitState.OPEN
        assert cb.state_name == "open"

    def test_force_close_transitions(self):
        cb = CircuitBreaker(name="test")
        cb.force_open()
        cb.force_close()
        assert cb.state == CircuitState.CLOSED

    def test_get_stats_after_force(self):
        cb = CircuitBreaker(name="test")
        cb.force_open()
        stats = cb.get_stats()
        assert stats["state"] == "open"
        assert stats["failure_count"] == cb._failure_threshold


class TestCoreCircuitBreakerCall:
    """Tests for call() success, failure, and transitions."""

    @pytest.mark.asyncio
    async def test_success_call_stays_closed(self):
        cb = CircuitBreaker(name="test")

        async def ok():
            return "ok"

        result = await cb.call(ok)
        assert result == "ok"
        assert cb.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_failure_threshold_reached_opens(self):
        cb = CircuitBreaker(name="test", failure_threshold=3)

        async def fail():
            raise ValueError("err")

        for i in range(3):
            with pytest.raises(ValueError):
                await cb.call(fail)

        assert cb.state == CircuitState.OPEN

    @pytest.mark.asyncio
    async def test_open_raises_circuit_breaker_error(self):
        cb = CircuitBreaker(name="test", failure_threshold=1, recovery_timeout=60)

        async def fail():
            raise ValueError("err")

        with pytest.raises(ValueError):
            await cb.call(fail)

        with pytest.raises(CircuitBreakerOpenError):
            await cb.call(fail)

    @pytest.mark.asyncio
    async def test_timeout_transitions_to_half_open(self):
        cb = CircuitBreaker(name="test", failure_threshold=1, recovery_timeout=0.02)

        async def fail():
            raise ValueError("err")

        with pytest.raises(ValueError):
            await cb.call(fail)

        time.sleep(0.03)

        async def ok():
            return "recovered"

        result = await cb.call(ok)
        assert result == "recovered"
        assert cb.state == CircuitState.HALF_OPEN

    @pytest.mark.asyncio
    async def test_half_open_success_closes(self):
        cb = CircuitBreaker(name="test", failure_threshold=1, recovery_timeout=0.02, success_threshold=1)

        async def fail():
            raise ValueError("err")

        with pytest.raises(ValueError):
            await cb.call(fail)

        time.sleep(0.03)

        async def ok():
            return "recovered"

        result = await cb.call(ok)
        assert result == "recovered"
        assert cb.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_half_open_failure_reopens(self):
        cb = CircuitBreaker(name="test", failure_threshold=1, recovery_timeout=0.02)

        async def fail():
            raise ValueError("err")

        with pytest.raises(ValueError):
            await cb.call(fail)

        time.sleep(0.03)

        async def still_fail():
            raise RuntimeError("nope")

        with pytest.raises(RuntimeError):
            await cb.call(still_fail)

        assert cb.state == CircuitState.OPEN

    @pytest.mark.asyncio
    async def test_half_open_max_requests_respected(self):
        cb = CircuitBreaker(name="test", failure_threshold=1, recovery_timeout=0.02, half_open_max_requests=1, success_threshold=3)

        async def fail():
            raise ValueError("err")

        with pytest.raises(ValueError):
            await cb.call(fail)

        time.sleep(0.03)

        async def ok():
            return "ok"

        result = await cb.call(ok)
        assert result == "ok"

        result = await cb.call(ok)
        assert result == "ok"

        with pytest.raises(CircuitBreakerOpenError):
            await cb.call(ok)

    @pytest.mark.asyncio
    async def test_sync_function_call(self):
        cb = CircuitBreaker(name="test")

        def sync_func():
            return "sync"

        result = await cb.call(sync_func)
        assert result == "sync"
        assert cb.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_failure_resets_success_count_in_half_open(self):
        cb = CircuitBreaker(name="test", failure_threshold=1, recovery_timeout=0.02, success_threshold=2)

        async def fail():
            raise ValueError("err")

        with pytest.raises(ValueError):
            await cb.call(fail)

        time.sleep(0.03)
        assert cb.state == CircuitState.OPEN

        async def ok():
            return "ok"

        await cb.call(ok)
        assert cb.state == CircuitState.HALF_OPEN

        with pytest.raises(ValueError):
            await cb.call(fail)

        assert cb.state == CircuitState.OPEN

    @pytest.mark.asyncio
    async def test_closed_success_resets_failure_count(self):
        cb = CircuitBreaker(name="test", failure_threshold=3)
        cb._failure_count = 2

        async def ok():
            return "ok"

        await cb.call(ok)
        assert cb._failure_count == 0

    @pytest.mark.asyncio
    async def test_get_stats_tracks_totals(self):
        cb = CircuitBreaker(name="test")

        async def ok():
            return "ok"

        await cb.call(ok)

        async def fail():
            raise ValueError("oops")

        with pytest.raises(ValueError):
            await cb.call(fail)

        stats = cb.get_stats()
        assert stats["total_calls"] == 2
        assert stats["total_successes"] == 1
        assert stats["total_failures"] == 1
        assert stats["name"] == "test"


class TestCoreCircuitBreakerRegistry:
    """Tests for CircuitBreakerRegistry."""

    def teardown_method(self):
        CircuitBreakerRegistry.reset_all()

    def test_shared_instance(self):
        cb1 = CircuitBreakerRegistry.get("svc")
        cb2 = CircuitBreakerRegistry.get("svc")
        assert cb1 is cb2

    def test_different_names_different_breakers(self):
        cb1 = CircuitBreakerRegistry.get("svc-a")
        cb2 = CircuitBreakerRegistry.get("svc-b")
        assert cb1 is not cb2

    def test_all_stats_empty_after_reset(self):
        CircuitBreakerRegistry.reset_all()
        assert CircuitBreakerRegistry.all_stats() == {}

    def test_all_stats_returns_all(self):
        CircuitBreakerRegistry.reset_all()
        CircuitBreakerRegistry.get("svc-a")
        CircuitBreakerRegistry.get("svc-b")
        stats = CircuitBreakerRegistry.all_stats()
        assert "svc-a" in stats
        assert "svc-b" in stats

    def test_custom_params_passed_through(self):
        CircuitBreakerRegistry.reset_all()
        cb = CircuitBreakerRegistry.get("custom", failure_threshold=3, recovery_timeout=15.0)
        assert cb._failure_threshold == 3
        assert cb._recovery_timeout == 15.0


class TestCoreCircuitBreakerEdgeCases:
    """Edge cases for CircuitBreaker."""

    def test_reset_clears_all_counters(self):
        cb = CircuitBreaker(name="test")
        cb._failure_count = 5
        cb._success_count = 3
        cb._half_open_requests = 2
        cb._reset()
        assert cb._failure_count == 0
        assert cb._success_count == 0
        assert cb._half_open_requests == 0

    @pytest.mark.asyncio
    async def test_force_open_then_force_close_cycle(self):
        cb = CircuitBreaker(name="test")
        cb.force_open()
        assert cb.state == CircuitState.OPEN

        cb.force_close()
        assert cb.state == CircuitState.CLOSED

        async def ok():
            return "works"

        result = await cb.call(ok)
        assert result == "works"

    @pytest.mark.asyncio
    async def test_call_after_force_open_raises(self):
        cb = CircuitBreaker(name="test", failure_threshold=5, recovery_timeout=600)
        cb.force_open()

        async def ok():
            return "ok"

        with pytest.raises(CircuitBreakerOpenError):
            await cb.call(ok)

    def test_force_open_sets_last_state_change(self):
        cb = CircuitBreaker(name="test")
        old_time = cb._last_state_change
        time.sleep(0.001)
        cb.force_open()
        assert cb._last_state_change > old_time
