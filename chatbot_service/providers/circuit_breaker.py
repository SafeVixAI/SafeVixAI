# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

import logging
import time

logger = logging.getLogger(__name__)

class CircuitBreaker:
    """Enterprise-grade Circuit Breaker with Closed, Open, and Half-Open states."""

    def __init__(self, failure_threshold: int = 3, recovery_timeout: int = 30):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self._failures: dict[str, int] = {}
        self._unavailable_until: dict[str, float] = {}

    def is_available(self, provider_name: str) -> bool:
        if provider_name == 'template':
            return True

        until = self._unavailable_until.get(provider_name)
        if until is not None:
            if time.time() < until:
                return False
            # Half-Open state (timeout passed, allowed to try once)
            self._unavailable_until.pop(provider_name, None)

        return True

    def record_failure(self, provider_name: str, duration: int = 0) -> None:
        """Record a failure and optionally force an open state for a specific duration."""
        if provider_name == 'template':
            return

        self._failures[provider_name] = self._failures.get(provider_name, 0) + 1

        # If duration is explicitly provided (e.g. rate limit retry-after) or threshold reached
        if duration > 0 or self._failures[provider_name] >= self.failure_threshold:
            open_duration = duration if duration > 0 else self.recovery_timeout
            self._unavailable_until[provider_name] = time.time() + open_duration
            logger.warning("CircuitBreaker tripped for %s (duration=%ss)", provider_name, open_duration)

    def record_success(self, provider_name: str) -> None:
        """Record a success, resetting failures (Close state)."""
        self._failures.pop(provider_name, None)
        self._unavailable_until.pop(provider_name, None)


class TokenBucket:
    """Token Bucket rate limiter for individual provider quota management."""
    def __init__(self, capacity: int = 10, refill_rate: float = 1.0):
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens: float = float(capacity)
        self.last_refill: float = time.monotonic()

    def allow(self, tokens_needed: int = 1) -> bool:
        now = time.monotonic()
        elapsed = now - self.last_refill
        self.tokens = min(float(self.capacity), self.tokens + elapsed * self.refill_rate)
        self.last_refill = now

        if self.tokens >= tokens_needed:
            self.tokens -= tokens_needed
            return True
        return False

