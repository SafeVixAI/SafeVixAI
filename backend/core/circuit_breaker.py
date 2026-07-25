# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

import inspect
import logging
import time
from collections.abc import Callable
from enum import Enum
from typing import Any

logger = logging.getLogger("safevixai.circuit_breaker")


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        half_open_max_requests: int = 3,
        success_threshold: int = 2,
    ):
        self.name = name
        self._failure_threshold = failure_threshold
        self._recovery_timeout = recovery_timeout
        self._half_open_max_requests = half_open_max_requests
        self._success_threshold = success_threshold

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: float | None = None
        self._half_open_requests = 0
        self._total_calls = 0
        self._total_failures = 0
        self._total_successes = 0
        self._last_state_change: float = time.time()

    @property
    def state(self) -> CircuitState:
        return self._state

    @property
    def state_name(self) -> str:
        return self._state.value

    def _transition_to(self, new_state: CircuitState) -> None:
        old_state = self._state
        self._state = new_state
        self._last_state_change = time.time()
        logger.info(
            "Circuit breaker '%s': %s -> %s",
            self.name,
            old_state.value,
            new_state.value,
        )

    def _reset(self) -> None:
        self._failure_count = 0
        self._success_count = 0
        self._half_open_requests = 0

    def _should_allow(self) -> bool:
        if self._state == CircuitState.CLOSED:
            return True

        if self._state == CircuitState.OPEN:
            if time.time() - self._last_state_change >= self._recovery_timeout:
                self._transition_to(CircuitState.HALF_OPEN)
                self._reset()
                return True
            return False

        if self._state == CircuitState.HALF_OPEN:
            if self._half_open_requests < self._half_open_max_requests:
                self._half_open_requests += 1
                return True
            return False

        return False

    async def call(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        self._total_calls += 1

        if not self._should_allow():
            self._total_failures += 1
            msg = (
                f"Circuit breaker '{self.name}' is OPEN. "
                f"Retry after {self._recovery_timeout - (time.time() - self._last_state_change):.0f}s"
            )
            raise CircuitBreakerOpenError(
                msg
            )

        try:
            if inspect.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            self._on_success()
            return result

        except Exception as e:
            self._on_failure(e)
            raise

    def _on_success(self) -> None:
        self._total_successes += 1

        if self._state == CircuitState.HALF_OPEN:
            self._success_count += 1
            if self._success_count >= self._success_threshold:
                self._transition_to(CircuitState.CLOSED)
                self._reset()

        if self._state == CircuitState.CLOSED:
            self._failure_count = 0

    def _on_failure(self, _exception: Exception) -> None:
        self._total_failures += 1
        self._failure_count += 1
        self._last_failure_time = time.time()

        if self._state == CircuitState.HALF_OPEN:
            self._transition_to(CircuitState.OPEN)
            self._reset()
            return

        if self._state == CircuitState.CLOSED and self._failure_count >= self._failure_threshold:
            self._transition_to(CircuitState.OPEN)
            self._reset()

    def force_open(self) -> None:
        self._state = CircuitState.OPEN
        self._last_state_change = time.time()
        self._failure_count = self._failure_threshold
        logger.info("Circuit breaker '%s': forced -> open", self.name)

    def force_close(self) -> None:
        self._state = CircuitState.CLOSED
        self._last_state_change = time.time()
        self._reset()
        logger.info("Circuit breaker '%s': forced -> closed", self.name)

    def get_stats(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "state": self.state_name,
            "failure_count": self._failure_count,
            "success_count": self._success_count,
            "total_calls": self._total_calls,
            "total_failures": self._total_failures,
            "total_successes": self._total_successes,
            "failure_threshold": self._failure_threshold,
            "recovery_timeout": self._recovery_timeout,
            "last_failure_time": self._last_failure_time,
            "last_state_change": self._last_state_change,
        }


class CircuitBreakerOpenError(Exception):
    pass


class CircuitBreakerRegistry:
    _breakers: dict[str, CircuitBreaker] = {}

    @classmethod
    def get(cls, name: str, **kwargs: Any) -> CircuitBreaker:
        if name not in cls._breakers:
            cls._breakers[name] = CircuitBreaker(name=name, **kwargs)
        return cls._breakers[name]

    @classmethod
    def all_stats(cls) -> dict[str, dict[str, Any]]:
        return {name: breaker.get_stats() for name, breaker in cls._breakers.items()}

    @classmethod
    def reset_all(cls) -> None:
        cls._breakers.clear()
