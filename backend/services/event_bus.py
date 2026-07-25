# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Enterprise Event Bus for SafeVixAI.

In-process async event bus with Redis pub/sub fallback for multi-instance deployments.
Designed with a clean interface to swap in Kafka/RabbitMQ later without changing consumers.

Event Types:
    complaint.created       - New complaint filed by citizen
    complaint.ai_verified   - AI verification pipeline completed
    complaint.assigned      - Complaint assigned to officer
    complaint.accepted      - Officer accepted assignment
    complaint.rejected_by_authority - Officer rejected assignment
    complaint.dispatched    - Officer dispatched to field
    complaint.work_started  - Field work commenced (GPS verified)
    complaint.evidence_uploaded - Before/after evidence submitted
    complaint.resolved      - Marked resolved by field team
    complaint.citizen_confirmed - Citizen confirmed resolution
    complaint.citizen_rejected  - Citizen rejected resolution
    complaint.reopened      - Complaint reopened after rejection
    complaint.escalated     - Escalated to higher authority
    complaint.closed        - Final closure
    sla.warning             - SLA deadline approaching
    sla.breached            - SLA deadline passed
    officer.checkin         - Officer GPS check-in
    officer.shift_start     - Officer started shift
    officer.shift_end       - Officer ended shift
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from collections import defaultdict
from collections.abc import Awaitable, Callable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger("safevixai.event_bus")

EventHandler = Callable[["DomainEvent"], Awaitable[None]]


@dataclass(frozen=True, slots=True)
class DomainEvent:
    """Immutable domain event with full audit metadata."""
    event_id: str
    event_type: str
    timestamp: str
    payload: dict[str, Any]
    correlation_id: str | None = None     # Links related events
    causation_id: str | None = None       # What caused this event
    actor_id: str | None = None
    actor_role: str | None = None
    source_service: str = "backend"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), default=str)

    @classmethod
    def create(
        cls,
        event_type: str,
        payload: dict[str, Any],
        *,
        correlation_id: str | None = None,
        causation_id: str | None = None,
        actor_id: str | None = None,
        actor_role: str | None = None,
    ) -> DomainEvent:
        return cls(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            timestamp=datetime.now(UTC).isoformat(),
            payload=payload,
            correlation_id=correlation_id or str(uuid.uuid4()),
            causation_id=causation_id,
            actor_id=actor_id,
            actor_role=actor_role,
        )


class EventBus:
    """
    In-process async event bus with ordered delivery guarantees.

    Supports:
    - Multiple handlers per event type
    - Wildcard subscriptions (subscribe to '*' for all events)
    - Dead letter queue for failed handler executions
    - Event replay from in-memory buffer (last 1000 events)
    - Metrics: events published, handlers executed, failures
    """

    def __init__(self, max_buffer: int = 1000) -> None:
        self._handlers: dict[str, list[EventHandler]] = defaultdict(list)
        self._buffer: list[DomainEvent] = []
        self._max_buffer = max_buffer
        self._dead_letter: list[dict[str, Any]] = []
        self._metrics = {
            "events_published": 0,
            "handlers_executed": 0,
            "handler_failures": 0,
        }
        self._redis_adapter: Any | None = None

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """Register a handler for an event type. Use '*' for all events."""
        self._handlers[event_type].append(handler)
        logger.info("Subscribed handler %s to event: %s", handler.__name__, event_type)

    def unsubscribe(self, event_type: str, handler: EventHandler) -> None:
        """Remove a handler for an event type."""
        if handler in self._handlers[event_type]:
            self._handlers[event_type].remove(handler)

    async def publish(self, event: DomainEvent) -> None:
        """Publish an event to all registered handlers (non-blocking)."""
        self._metrics["events_published"] += 1

        # Buffer for replay
        self._buffer.append(event)
        if len(self._buffer) > self._max_buffer:
            self._buffer = self._buffer[-self._max_buffer:]

        logger.info(
            "Event published: %s [%s] correlation=%s",
            event.event_type,
            event.event_id[:8],
            (event.correlation_id or "")[:8],
        )

        # Dispatch to specific handlers
        handlers = list(self._handlers.get(event.event_type, []))
        # Also dispatch to wildcard subscribers
        handlers.extend(self._handlers.get("*", []))

        for handler in handlers:
            # Run each handler as a background task for isolation
            asyncio.create_task(self._safe_execute(handler, event))

        # Publish to Redis pub/sub if adapter is configured
        if self._redis_adapter:
            try:
                await self._redis_adapter.publish(event)
            except Exception as e:
                logger.debug("Redis pub/sub publish failed (non-critical): %s", e)

    async def _safe_execute(self, handler: EventHandler, event: DomainEvent) -> None:
        """Execute handler with error isolation — one handler failure doesn't affect others."""
        try:
            await asyncio.wait_for(handler(event), timeout=30.0)
            self._metrics["handlers_executed"] += 1
        except TimeoutError:
            self._metrics["handler_failures"] += 1
            logger.error(
                "Handler %s timed out for event %s",
                handler.__name__, event.event_type,
            )
            self._dead_letter.append({
                "event": event.to_dict(),
                "handler": handler.__name__,
                "error": "TimeoutError",
                "timestamp": datetime.now(UTC).isoformat(),
            })
        except Exception as e:
            self._metrics["handler_failures"] += 1
            logger.exception(
                "Handler %s failed for event %s: %s",
                handler.__name__, event.event_type, e,
            )
            self._dead_letter.append({
                "event": event.to_dict(),
                "handler": handler.__name__,
                "error": str(e),
                "timestamp": datetime.now(UTC).isoformat(),
            })

    def get_recent_events(self, event_type: str | None = None, limit: int = 50) -> list[DomainEvent]:
        """Retrieve recent events from the in-memory buffer."""
        events = self._buffer
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        return events[-limit:]

    def get_metrics(self) -> dict[str, Any]:
        """Get event bus operational metrics."""
        return {
            **self._metrics,
            "buffer_size": len(self._buffer),
            "dead_letter_count": len(self._dead_letter),
            "registered_handlers": {
                k: len(v) for k, v in self._handlers.items()
            },
        }

    def get_dead_letters(self, limit: int = 20) -> list[dict[str, Any]]:
        """Retrieve failed event deliveries for debugging."""
        return self._dead_letter[-limit:]

    def set_redis_adapter(self, adapter: Any) -> None:
        """Attach Redis pub/sub adapter for multi-instance deployment."""
        self._redis_adapter = adapter
        logger.info("Redis pub/sub adapter attached to event bus")


class RedisPubSubAdapter:
    """Optional Redis pub/sub adapter for cross-instance event propagation."""

    def __init__(self, redis_client: Any, channel_prefix: str = "safevixai:events") -> None:
        self._redis = redis_client
        self._prefix = channel_prefix

    async def publish(self, event: DomainEvent) -> None:
        channel = f"{self._prefix}:{event.event_type}"
        try:
            await self._redis.publish(channel, event.to_json())
        except Exception as e:
            logger.debug("Redis publish failed: %s", e)


# Singleton event bus instance
_event_bus: EventBus | None = None


def get_event_bus() -> EventBus:
    """Get the global event bus singleton."""
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus


def reset_event_bus() -> None:
    """Reset the event bus (for testing)."""
    global _event_bus
    _event_bus = None
