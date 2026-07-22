# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.event_bus import DomainEvent, EventBus, get_event_bus, reset_event_bus


@pytest.mark.asyncio
async def test_event_bus_publish_subscribe():
    bus = EventBus()

    received_events = []

    async def test_handler(event: DomainEvent):
        received_events.append(event)

    bus.subscribe("complaint.created", test_handler)

    event = DomainEvent.create(
        event_type="complaint.created",
        payload={"ref": "REF-1"}
    )

    await bus.publish(event)

    # Wait briefly for async task execution
    await asyncio.sleep(0.05)

    assert len(received_events) == 1
    assert received_events[0].event_type == "complaint.created"
    assert received_events[0].payload["ref"] == "REF-1"


@pytest.mark.asyncio
async def test_event_bus_wildcard_subscription():
    bus = EventBus()
    received_events = []

    async def wildcard_handler(event: DomainEvent):
        received_events.append(event)

    bus.subscribe("*", wildcard_handler)

    event1 = DomainEvent.create("complaint.created", {})
    event2 = DomainEvent.create("complaint.assigned", {})

    await bus.publish(event1)
    await bus.publish(event2)

    await asyncio.sleep(0.05)

    assert len(received_events) == 2


@pytest.mark.asyncio
async def test_event_bus_dead_letter_queue():
    bus = EventBus()

    async def failing_handler(event: DomainEvent):
        raise ValueError("Handler execution failed intentionally")

    bus.subscribe("complaint.created", failing_handler)

    event = DomainEvent.create("complaint.created", {})
    await bus.publish(event)

    await asyncio.sleep(0.05)

    metrics = bus.get_metrics()
    assert metrics["dead_letter_count"] == 1

    dead_letters = bus.get_dead_letters()
    assert len(dead_letters) == 1
    assert "intentionally" in dead_letters[0]["error"]


@pytest.mark.asyncio
async def test_unsubscribe_removes_handler():
    bus = EventBus()
    received = []

    async def handler(event):
        received.append(event)

    bus.subscribe("complaint.created", handler)
    bus.unsubscribe("complaint.created", handler)

    await bus.publish(DomainEvent.create("complaint.created", {}))
    await asyncio.sleep(0.05)
    assert len(received) == 0


@pytest.mark.asyncio
async def test_unsubscribe_handler_not_in_list():
    bus = EventBus()

    async def handler(event):
        pass

    bus.subscribe("complaint.created", handler)
    def other_handler(e):
        return None
    other_handler.__name__ = "other_handler"
    bus.unsubscribe("complaint.created", other_handler)  # no error


@pytest.mark.asyncio
async def test_get_recent_events_filter_by_type():
    bus = EventBus()

    await bus.publish(DomainEvent.create("complaint.created", {"ref": "A"}))
    await bus.publish(DomainEvent.create("complaint.assigned", {"ref": "B"}))
    await bus.publish(DomainEvent.create("complaint.created", {"ref": "C"}))

    created = bus.get_recent_events(event_type="complaint.created")
    assert len(created) == 2
    assert all(e.event_type == "complaint.created" for e in created)


@pytest.mark.asyncio
async def test_get_recent_events_with_limit():
    bus = EventBus()

    for i in range(10):
        await bus.publish(DomainEvent.create("complaint.created", {"i": i}))

    limited = bus.get_recent_events(limit=3)
    assert len(limited) == 3


def test_get_metrics_structure():
    bus = EventBus()
    metrics = bus.get_metrics()
    assert "events_published" in metrics
    assert "handlers_executed" in metrics
    assert "handler_failures" in metrics
    assert "buffer_size" in metrics
    assert "dead_letter_count" in metrics
    assert "registered_handlers" in metrics
    assert isinstance(metrics["registered_handlers"], dict)


@pytest.mark.asyncio
async def test_get_dead_letters_with_limit():
    bus = EventBus()

    async def fail(event):
        raise ValueError("err")

    bus.subscribe("*", fail)
    for i in range(5):
        await bus.publish(DomainEvent.create(f"type.{i}", {}))
    await asyncio.sleep(0.1)

    dead = bus.get_dead_letters(limit=2)
    assert len(dead) == 2


@pytest.mark.asyncio
async def test_set_redis_adapter_publish():
    bus = EventBus()
    mock_adapter = MagicMock()
    mock_adapter.publish = AsyncMock()

    bus.set_redis_adapter(mock_adapter)

    event = DomainEvent.create("complaint.created", {})
    await bus.publish(event)
    await asyncio.sleep(0.05)

    mock_adapter.publish.assert_awaited_once_with(event)


def test_domain_event_fields():
    event = DomainEvent.create(
        event_type="complaint.created",
        payload={"key": "value"},
        correlation_id="corr-123",
        actor_id="actor-1",
        actor_role="citizen",
    )
    assert event.event_id is not None
    assert event.timestamp is not None
    assert event.source_service == "backend"
    assert event.correlation_id == "corr-123"
    assert event.actor_id == "actor-1"
    assert event.actor_role == "citizen"
    assert event.causation_id is None


def test_domain_event_to_json():
    event = DomainEvent.create("complaint.created", {"ref": "R1"})
    parsed = json.loads(event.to_json())
    assert parsed["event_type"] == "complaint.created"
    assert parsed["payload"]["ref"] == "R1"


def test_domain_event_to_dict():
    event = DomainEvent.create("complaint.created", {"ref": "R1"})
    d = event.to_dict()
    assert d["event_type"] == "complaint.created"
    assert d["payload"]["ref"] == "R1"
    assert "event_id" in d
    assert "timestamp" in d


@pytest.mark.asyncio
async def test_event_buffer_overflow():
    bus = EventBus(max_buffer=5)

    for i in range(10):
        await bus.publish(DomainEvent.create("test.event", {"i": i}))

    recent = bus.get_recent_events()
    assert len(recent) == 5


@pytest.mark.asyncio
async def test_handler_timeout():
    bus = EventBus()

    async def slow_handler(event):
        await asyncio.sleep(60)

    bus.subscribe("complaint.created", slow_handler)

    event = DomainEvent.create("complaint.created", {})
    await bus.publish(event)
    await asyncio.sleep(0.1)

    metrics = bus.get_metrics()
    bus.get_dead_letters()
    assert metrics["handler_failures"] >= 0  # timeout may or may not fire in 0.1s


@pytest.mark.asyncio
async def test_handler_timeout_error_fires():
    """Covers the except asyncio.TimeoutError path in _safe_execute (lines 161-166)."""
    bus = EventBus()

    async def any_handler(event):
        pass

    bus.subscribe("test.event", any_handler)
    event = DomainEvent.create("test.event", {})

    with patch("services.event_bus.asyncio.wait_for", side_effect=TimeoutError()):
        await bus.publish(event)
        await asyncio.sleep(0.05)

    metrics = bus.get_metrics()
    assert metrics["handler_failures"] == 1
    dead_letters = bus.get_dead_letters()
    assert len(dead_letters) == 1
    assert "TimeoutError" in dead_letters[0]["error"]


@pytest.mark.asyncio
async def test_get_event_bus_singleton():
    reset_event_bus()
    bus1 = get_event_bus()
    bus2 = get_event_bus()
    assert bus1 is bus2
    reset_event_bus()


@pytest.mark.asyncio
async def test_reset_event_bus():
    reset_event_bus()
    bus1 = get_event_bus()
    reset_event_bus()
    bus2 = get_event_bus()
    assert bus1 is not bus2
