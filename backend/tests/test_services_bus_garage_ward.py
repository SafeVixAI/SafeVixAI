# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team
"""Service layer coverage: event_bus, garage_service, ward_service, data_retention.

Combined deep-coverage suite targeting edge cases and paths not covered by
the individual per-service test files:
  - test_event_bus.py
  - test_garage_service.py
  - test_ward_service.py
  - test_service_data_retention.py
"""

from __future__ import annotations

import asyncio
import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from models.ward import Ward
from services.data_retention import DataRetentionScheduler
from services.event_bus import DomainEvent, EventBus, get_event_bus, reset_event_bus
from services.exceptions import ServiceValidationError
from services.garage_service import GarageService
from services.ward_service import GCC_DEMO_WARDS, WardService

# ---------------------------------------------------------------------------
# Module-level autouse: reset singleton before/after every test so that
# singleton tests cannot bleed into each other.
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _reset_event_bus_singleton():
    reset_event_bus()
    yield
    reset_event_bus()


# ===========================================================================
# Section 1 — DomainEvent
# ===========================================================================


class TestDomainEvent:
    """Edge-case and field-level tests for the immutable DomainEvent dataclass."""

    def test_create_auto_generates_correlation_id_as_uuid(self):
        """When no correlation_id is supplied, create() generates a valid UUID."""
        event = DomainEvent.create("complaint.created", {"ref": "R0"})
        assert event.correlation_id is not None
        # Must not raise — proves it is a valid UUID string
        uuid.UUID(event.correlation_id)

    def test_create_explicit_correlation_id_is_preserved(self):
        corr = str(uuid.uuid4())
        event = DomainEvent.create("complaint.assigned", {}, correlation_id=corr)
        assert event.correlation_id == corr

    def test_create_with_explicit_causation_id(self):
        cause = str(uuid.uuid4())
        event = DomainEvent.create("complaint.resolved", {}, causation_id=cause)
        assert event.causation_id == cause

    def test_create_causation_id_defaults_to_none(self):
        event = DomainEvent.create("sla.warning", {})
        assert event.causation_id is None

    def test_create_source_service_default_is_backend(self):
        event = DomainEvent.create("officer.checkin", {})
        assert event.source_service == "backend"

    def test_create_actor_fields_propagated(self):
        event = DomainEvent.create(
            "complaint.dispatched",
            {},
            actor_id="usr-99",
            actor_role="officer",
        )
        assert event.actor_id == "usr-99"
        assert event.actor_role == "officer"

    def test_create_two_events_have_unique_event_ids(self):
        e1 = DomainEvent.create("type.x", {})
        e2 = DomainEvent.create("type.x", {})
        assert e1.event_id != e2.event_id

    def test_to_dict_contains_all_nine_required_keys(self):
        event = DomainEvent.create(
            "sla.breached", {"minutes": 5}, actor_id="u1", actor_role="admin"
        )
        d = event.to_dict()
        for key in (
            "event_id",
            "event_type",
            "timestamp",
            "payload",
            "correlation_id",
            "causation_id",
            "actor_id",
            "actor_role",
            "source_service",
        ):
            assert key in d, f"Missing key: {key}"

    def test_to_json_produces_valid_json_roundtrip(self):
        event = DomainEvent.create("complaint.citizen_confirmed", {"id": 42})
        parsed = json.loads(event.to_json())
        assert parsed["event_type"] == "complaint.citizen_confirmed"
        assert parsed["payload"]["id"] == 42
        assert parsed["source_service"] == "backend"

    def test_frozen_dataclass_rejects_mutation(self):
        event = DomainEvent.create("test.event", {})
        with pytest.raises((AttributeError, TypeError)):
            event.event_type = "mutated"  # type: ignore[misc]


# ===========================================================================
# Section 2 — EventBus: subscribe / unsubscribe / publish
# ===========================================================================


class TestEventBusCoreOperations:
    """Targeted tests for handler registration, dispatch, and adapter wiring."""

    @pytest.mark.asyncio
    async def test_subscribe_multiple_handlers_same_event_both_called(self):
        bus = EventBus()
        received_a: list = []
        received_b: list = []

        async def handler_a(e):
            received_a.append(e)

        async def handler_b(e):
            received_b.append(e)

        bus.subscribe("complaint.created", handler_a)
        bus.subscribe("complaint.created", handler_b)

        await bus.publish(DomainEvent.create("complaint.created", {}))
        await asyncio.sleep(0.06)

        assert len(received_a) == 1
        assert len(received_b) == 1

    @pytest.mark.asyncio
    async def test_specific_handler_not_invoked_by_other_event_type(self):
        bus = EventBus()
        received: list = []

        async def h(e):
            received.append(e)

        bus.subscribe("complaint.created", h)
        await bus.publish(DomainEvent.create("complaint.resolved", {}))
        await asyncio.sleep(0.05)

        assert received == []

    @pytest.mark.asyncio
    async def test_unsubscribe_nonexistent_handler_is_noop(self):
        """Removing a handler that was never subscribed must not raise."""
        bus = EventBus()

        async def registered(e):
            pass

        async def stranger(e):
            pass

        bus.subscribe("type.a", registered)
        # Should not raise
        bus.unsubscribe("type.a", stranger)

    @pytest.mark.asyncio
    async def test_publish_dispatches_to_specific_handler(self):
        bus = EventBus()
        received: list = []

        async def h(e):
            received.append(e.payload["v"])

        bus.subscribe("officer.shift_start", h)

        await bus.publish(DomainEvent.create("officer.shift_start", {"v": 7}))
        await asyncio.sleep(0.05)

        assert received == [7]

    @pytest.mark.asyncio
    async def test_publish_dispatches_to_wildcard_handler(self):
        bus = EventBus()
        received: list = []

        async def catch_all(e):
            received.append(e.event_type)

        bus.subscribe("*", catch_all)

        await bus.publish(DomainEvent.create("alpha", {}))
        await bus.publish(DomainEvent.create("beta", {}))
        await asyncio.sleep(0.05)

        assert sorted(received) == ["alpha", "beta"]

    @pytest.mark.asyncio
    async def test_publish_increments_events_published_counter(self):
        bus = EventBus()
        for _ in range(3):
            await bus.publish(DomainEvent.create("tick", {}))
        assert bus.get_metrics()["events_published"] == 3

    @pytest.mark.asyncio
    async def test_publish_adds_event_to_buffer(self):
        bus = EventBus()
        event = DomainEvent.create("sla.warning", {"eta": 10})
        await bus.publish(event)
        assert event in bus._buffer

    @pytest.mark.asyncio
    async def test_redis_adapter_receives_published_event(self):
        bus = EventBus()
        adapter = MagicMock()
        adapter.publish = AsyncMock()
        bus.set_redis_adapter(adapter)

        event = DomainEvent.create("complaint.escalated", {"priority": "HIGH"})
        await bus.publish(event)

        adapter.publish.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_redis_adapter_failure_is_silenced_no_exception(self):
        """A Redis publish failure must not propagate to the caller."""
        bus = EventBus()
        bad_adapter = MagicMock()
        bad_adapter.publish = AsyncMock(side_effect=ConnectionError("redis down"))
        bus.set_redis_adapter(bad_adapter)

        # Must complete without raising
        await bus.publish(DomainEvent.create("complaint.created", {}))

    def test_set_redis_adapter_stores_adapter_reference(self):
        bus = EventBus()
        adapter = object()
        bus.set_redis_adapter(adapter)
        assert bus._redis_adapter is adapter


# ===========================================================================
# Section 3 — EventBus: _safe_execute paths (direct invocation)
# ===========================================================================


class TestEventBusSafeExecute:
    """
    Tests that call _safe_execute directly to exercise the TimeoutError and
    Exception branches without waiting on asyncio.create_task timing.
    """

    @pytest.mark.asyncio
    async def test_success_increments_handlers_executed(self):
        bus = EventBus()

        async def good(e):
            pass

        event = DomainEvent.create("test.event", {})
        await bus._safe_execute(good, event)

        assert bus._metrics["handlers_executed"] == 1
        assert bus._metrics["handler_failures"] == 0
        assert bus.get_dead_letters() == []

    @pytest.mark.asyncio
    async def test_timeout_error_increments_failures_and_adds_dead_letter(self):
        bus = EventBus()

        async def slow(e):
            pass

        event = DomainEvent.create("test.timeout", {})

        async def raise_timeout(coro, *a, **kw):
            coro.close()  # discard coroutine cleanly to avoid RuntimeWarning
            raise TimeoutError()

        with patch("services.event_bus.asyncio.wait_for", raise_timeout):
            await bus._safe_execute(slow, event)

        assert bus._metrics["handler_failures"] == 1
        assert bus._metrics["handlers_executed"] == 0
        letters = bus.get_dead_letters()
        assert len(letters) == 1
        assert letters[0]["error"] == "TimeoutError"
        assert letters[0]["handler"] == "slow"

    @pytest.mark.asyncio
    async def test_exception_increments_failures_and_adds_dead_letter(self):
        bus = EventBus()

        async def broken(e):
            raise RuntimeError("handler blew up")

        event = DomainEvent.create("test.exception", {})
        await bus._safe_execute(broken, event)

        assert bus._metrics["handler_failures"] == 1
        letters = bus.get_dead_letters()
        assert len(letters) == 1
        assert "handler blew up" in letters[0]["error"]
        assert letters[0]["handler"] == "broken"

    @pytest.mark.asyncio
    async def test_dead_letter_entry_contains_event_dict_and_timestamp(self):
        bus = EventBus()

        async def fail(e):
            raise ValueError("bad state")

        event = DomainEvent.create("complaint.closed", {"ref": "X42"})
        await bus._safe_execute(fail, event)

        letter = bus.get_dead_letters()[0]
        assert letter["event"]["event_type"] == "complaint.closed"
        assert letter["event"]["payload"]["ref"] == "X42"
        assert "timestamp" in letter


# ===========================================================================
# Section 4 — EventBus: buffer, metrics, dead-letter pagination
# ===========================================================================


class TestEventBusBufferAndMetrics:
    @pytest.mark.asyncio
    async def test_get_recent_events_no_filter_returns_all(self):
        bus = EventBus()
        for t in ("a", "b", "c"):
            await bus.publish(DomainEvent.create(t, {}))
        assert len(bus.get_recent_events()) == 3

    @pytest.mark.asyncio
    async def test_get_recent_events_type_filter_returns_subset(self):
        bus = EventBus()
        await bus.publish(DomainEvent.create("type.x", {"n": 1}))
        await bus.publish(DomainEvent.create("type.y", {"n": 2}))
        await bus.publish(DomainEvent.create("type.x", {"n": 3}))

        result = bus.get_recent_events(event_type="type.x")
        assert len(result) == 2
        assert all(e.event_type == "type.x" for e in result)

    @pytest.mark.asyncio
    async def test_get_recent_events_limit_caps_results(self):
        bus = EventBus()
        for i in range(20):
            await bus.publish(DomainEvent.create("evt", {"i": i}))
        assert len(bus.get_recent_events(limit=4)) == 4

    @pytest.mark.asyncio
    async def test_get_recent_events_limit_on_filtered_type(self):
        bus = EventBus()
        for i in range(8):
            await bus.publish(DomainEvent.create("type.z", {"i": i}))
        result = bus.get_recent_events(event_type="type.z", limit=3)
        assert len(result) == 3
        assert result[-1].payload["i"] == 7  # most recent

    @pytest.mark.asyncio
    async def test_buffer_overflow_keeps_only_most_recent_n(self):
        bus = EventBus(max_buffer=3)
        for i in range(7):
            await bus.publish(DomainEvent.create("evt", {"i": i}))

        recent = bus.get_recent_events()
        assert len(recent) == 3
        # Oldest kept is index 4; most recent is index 6
        assert recent[0].payload["i"] == 4
        assert recent[-1].payload["i"] == 6

    def test_get_metrics_initial_state_all_zero(self):
        bus = EventBus()
        m = bus.get_metrics()
        assert m["events_published"] == 0
        assert m["handlers_executed"] == 0
        assert m["handler_failures"] == 0
        assert m["buffer_size"] == 0
        assert m["dead_letter_count"] == 0
        assert m["registered_handlers"] == {}

    def test_get_metrics_registered_handlers_counts_per_type(self):
        bus = EventBus()

        async def h1(e):
            pass

        async def h2(e):
            pass

        bus.subscribe("type.a", h1)
        bus.subscribe("type.a", h2)
        bus.subscribe("type.b", h1)

        m = bus.get_metrics()
        assert m["registered_handlers"]["type.a"] == 2
        assert m["registered_handlers"]["type.b"] == 1

    @pytest.mark.asyncio
    async def test_get_metrics_buffer_size_reflects_publish_count(self):
        bus = EventBus()
        for _ in range(5):
            await bus.publish(DomainEvent.create("t", {}))
        assert bus.get_metrics()["buffer_size"] == 5

    @pytest.mark.asyncio
    async def test_get_dead_letters_respects_limit_parameter(self):
        bus = EventBus()

        async def fail(e):
            raise ValueError("x")

        bus.subscribe("*", fail)

        for i in range(6):
            await bus.publish(DomainEvent.create(f"t.{i}", {}))
        await asyncio.sleep(0.12)

        # Default limit is 20, but we request 3
        assert len(bus.get_dead_letters(limit=3)) == 3


# ===========================================================================
# Section 5 — EventBus: singleton lifecycle
# ===========================================================================


class TestEventBusSingleton:
    def test_get_event_bus_returns_same_instance_on_repeated_calls(self):
        b1 = get_event_bus()
        b2 = get_event_bus()
        assert b1 is b2

    def test_reset_event_bus_causes_next_get_to_return_new_instance(self):
        b1 = get_event_bus()
        reset_event_bus()
        b2 = get_event_bus()
        assert b1 is not b2

    def test_autouse_fixture_ensures_clean_singleton_state(self):
        """The module-level autouse fixture must have cleared _event_bus to None."""
        import services.event_bus as eb_mod

        # get_event_bus() was not yet called this test → should be None
        assert eb_mod._event_bus is None


# ===========================================================================
# Section 6 — GarageService: _parse_state_code
# ===========================================================================


class TestGarageServiceParseStateCode:
    def test_empty_string_falls_back_to_dl(self):
        assert GarageService._parse_state_code("") == "DL"

    def test_gj_plate_extracts_gj(self):
        assert GarageService._parse_state_code("GJ-01-AA-1111") == "GJ"

    def test_wb_plate_extracts_wb(self):
        assert GarageService._parse_state_code("WB-22-BB-2222") == "WB"

    def test_digit_first_character_falls_back_to_dl(self):
        assert GarageService._parse_state_code("1A23BC4567") == "DL"

    def test_single_alpha_character_falls_back_to_dl(self):
        # len("A") < 2 → fallback
        assert GarageService._parse_state_code("A") == "DL"

    def test_lowercase_plate_is_normalized_before_extraction(self):
        assert GarageService._parse_state_code("up-32-cd-0001") == "UP"


# ===========================================================================
# Section 7 — GarageService: _generate_deterministic_vehicle
# ===========================================================================


class TestGarageServiceGenerateVehicle:
    def test_predefined_mh_plate_returns_priya_patel(self):
        v = GarageService._generate_deterministic_vehicle("MH-02-EF-9012")
        assert v["owner_name"] == "Priya Patel"
        assert v["vehicle_make"] == "Maruti Suzuki"
        assert v["rc_status"] == "ACTIVE"

    def test_predefined_ka_plate_returns_rahul_hegde(self):
        v = GarageService._generate_deterministic_vehicle("KA-51-GH-3456")
        assert v["owner_name"] == "Rahul Hegde"
        assert v["vehicle_model"] == "Creta"

    def test_hash_based_vehicle_make_is_in_known_list(self):
        from services.garage_service import MAKES_AND_MODELS

        valid_makes = {make for make, _ in MAKES_AND_MODELS}
        v = GarageService._generate_deterministic_vehicle("HR-26-ZZ-0001")
        assert v["vehicle_make"] in valid_makes

    def test_hash_based_vehicle_owner_is_in_known_list(self):
        from services.garage_service import OWNERS

        v = GarageService._generate_deterministic_vehicle("UP-80-AB-0001")
        assert v["owner_name"] in OWNERS

    def test_same_plate_always_returns_identical_record(self):
        v1 = GarageService._generate_deterministic_vehicle("PB-10-XY-5555")
        v2 = GarageService._generate_deterministic_vehicle("PB-10-XY-5555")
        assert v1 == v2

    def test_hash_based_record_has_all_required_keys(self):
        v = GarageService._generate_deterministic_vehicle("JK-02-AB-0042")
        for key in (
            "owner_name",
            "vehicle_make",
            "vehicle_model",
            "rc_status",
            "insurance_expiry_days",
            "puc_expiry_days",
            "created_days_ago",
        ):
            assert key in v

    def test_rc_status_only_active_or_suspended(self):
        for i in range(50):
            v = GarageService._generate_deterministic_vehicle(f"RJ-14-ZZ-{i:04d}")
            assert v["rc_status"] in ("ACTIVE", "SUSPENDED")


# ===========================================================================
# Section 8 — GarageService: sync_vehicles
# ===========================================================================


class TestGarageServiceSyncVehicles:
    @pytest.mark.asyncio
    async def test_vehicle_uuid_is_deterministic_same_user_and_plate(self):
        """uuid.uuid5(NAMESPACE_DNS, '{user}:{plate}') must be stable."""
        with patch.object(asyncio, "sleep", AsyncMock()):
            r1 = await GarageService.sync_vehicles("u-fixed", "GJ-01-AA-1111", cache=None)
            r2 = await GarageService.sync_vehicles("u-fixed", "GJ-01-AA-1111", cache=None)
        assert r1.vehicles[0].id == r2.vehicles[0].id

    @pytest.mark.asyncio
    async def test_different_user_same_plate_yields_different_uuid(self):
        with patch.object(asyncio, "sleep", AsyncMock()):
            r1 = await GarageService.sync_vehicles("user-aaa", "GJ-01-AA-1111", cache=None)
            r2 = await GarageService.sync_vehicles("user-bbb", "GJ-01-AA-1111", cache=None)
        assert r1.vehicles[0].id != r2.vehicles[0].id

    @pytest.mark.asyncio
    async def test_whitespace_around_plate_is_stripped(self):
        with patch.object(asyncio, "sleep", AsyncMock()):
            result = await GarageService.sync_vehicles("u", "  TN-01-AB-1234  ", cache=None)
        assert len(result.vehicles) == 1
        assert result.vehicles[0].vehicle_number == "TN-01-AB-1234"

    @pytest.mark.asyncio
    async def test_last_synced_at_is_datetime_object(self):
        from datetime import datetime

        with patch.object(asyncio, "sleep", AsyncMock()):
            result = await GarageService.sync_vehicles("u", "TN-01-AB-1234", cache=None)
        assert isinstance(result.last_synced_at, datetime)

    @pytest.mark.asyncio
    async def test_sync_status_is_always_completed(self):
        with patch.object(asyncio, "sleep", AsyncMock()):
            result = await GarageService.sync_vehicles("u", "DL-03-CD-5678", cache=None)
        assert result.sync_status == "COMPLETED"

    @pytest.mark.asyncio
    async def test_vehicle_insurance_and_puc_expiry_present(self):
        with patch.object(asyncio, "sleep", AsyncMock()):
            result = await GarageService.sync_vehicles("u", "TN-01-AB-1234", cache=None)
        v = result.vehicles[0]
        assert v.insurance_expiry is not None
        assert v.puc_expiry is not None

    @pytest.mark.asyncio
    async def test_cache_set_json_failure_does_not_drop_vehicle(self):
        """An exception in cache.set_json must not prevent the vehicle from appearing."""
        cache = AsyncMock()
        cache.get_json.return_value = None
        cache.set_json.side_effect = Exception("write failed")

        with patch.object(asyncio, "sleep", AsyncMock()):
            result = await GarageService.sync_vehicles("u", "GJ-01-AA-1111", cache=cache)

        assert len(result.vehicles) == 1
        cache.set_json.assert_called_once()  # attempted

    @pytest.mark.asyncio
    async def test_no_plate_returns_two_predefined_default_vehicles(self):
        with patch.object(asyncio, "sleep", AsyncMock()):
            result = await GarageService.sync_vehicles("u", vehicle_number=None, cache=None)
        plates = [v.vehicle_number for v in result.vehicles]
        assert plates == ["TN-01-AB-1234", "DL-03-CD-5678"]

    @pytest.mark.asyncio
    async def test_invalid_plate_short_string_raises_validation_error(self):
        with pytest.raises(ServiceValidationError, match="Invalid Indian vehicle"):
            await GarageService.sync_vehicles("u", "BADPLATE", cache=None)

    @pytest.mark.asyncio
    async def test_invalid_plate_numeric_prefix_raises_validation_error(self):
        with pytest.raises(ServiceValidationError):
            await GarageService.sync_vehicles("u", "12-34-AB-5678", cache=None)

    @pytest.mark.asyncio
    async def test_cache_get_json_exception_falls_through_to_generation(self):
        """A Redis read failure must not crash sync — it falls through to generation."""
        cache = AsyncMock()
        cache.get_json.side_effect = ConnectionError("redis timeout")

        with patch.object(asyncio, "sleep", AsyncMock()):
            result = await GarageService.sync_vehicles("u", "DL-03-CD-5678", cache=cache)

        assert result.sync_status == "COMPLETED"
        assert len(result.vehicles) == 1
        assert result.vehicles[0].vehicle_number == "DL-03-CD-5678"

    @pytest.mark.asyncio
    async def test_cache_hit_skips_generation_and_uses_cached_owner(self):
        cached = {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "vehicle_number": "TN-01-AB-1234",
            "owner_name": "Cached Person",
            "vehicle_make": "TATA",
            "vehicle_model": "Nexon EV",
            "rc_status": "ACTIVE",
            "insurance_expiry": "2027-01-01T00:00:00",
            "puc_expiry": "2026-12-01T00:00:00",
            "created_at": "2025-01-01T00:00:00",
        }
        cache = AsyncMock()
        cache.get_json.return_value = cached

        with patch.object(asyncio, "sleep", AsyncMock()):
            result = await GarageService.sync_vehicles("u", "TN-01-AB-1234", cache=cache)

        assert result.vehicles[0].owner_name == "Cached Person"
        # set_json must NOT be called on a cache hit
        cache.set_json.assert_not_called()


# ===========================================================================
# Section 9 — WardService: seeding logic
# ===========================================================================


class TestWardServiceSeeding:
    @pytest.mark.asyncio
    async def test_ensure_seeded_empty_db_adds_five_wards_and_commits(self):
        db = AsyncMock()
        db.add = MagicMock()  # session.add() is synchronous in SQLAlchemy
        count_mock = MagicMock()
        count_mock.scalar.return_value = 0
        db.execute = AsyncMock(return_value=count_mock)

        await WardService.ensure_seeded(db)

        assert db.add.call_count == 5
        db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_ensure_seeded_none_scalar_treated_as_zero_triggers_seed(self):
        """scalar() returning None (NULL COUNT) must still trigger seeding via `or 0`."""
        db = AsyncMock()
        db.add = MagicMock()  # session.add() is synchronous in SQLAlchemy
        count_mock = MagicMock()
        count_mock.scalar.return_value = None  # None or 0 → 0
        db.execute = AsyncMock(return_value=count_mock)

        await WardService.ensure_seeded(db)

        assert db.add.call_count == 5

    @pytest.mark.asyncio
    async def test_ensure_seeded_nonempty_db_skips_seeding(self):
        db = AsyncMock()
        db.add = MagicMock()  # session.add() is synchronous in SQLAlchemy
        count_mock = MagicMock()
        count_mock.scalar.return_value = 3
        db.execute = AsyncMock(return_value=count_mock)

        await WardService.ensure_seeded(db)

        db.add.assert_not_called()
        db.commit.assert_not_called()

    def test_gcc_demo_wards_count_is_exactly_five(self):
        assert len(GCC_DEMO_WARDS) == 5

    def test_gcc_demo_wards_all_in_chennai_tamil_nadu(self):
        assert all(w["city"] == "Chennai" for w in GCC_DEMO_WARDS)
        assert all(w["state_code"] == "TN" for w in GCC_DEMO_WARDS)

    def test_gcc_demo_wards_each_has_polygon_boundary_wkt(self):
        for w in GCC_DEMO_WARDS:
            assert w["boundary_wkt"].startswith("POLYGON(("), f"Ward {w['ward_id']} has invalid WKT"

    def test_gcc_demo_wards_have_unique_ward_ids(self):
        ids = [w["ward_id"] for w in GCC_DEMO_WARDS]
        assert len(ids) == len(set(ids)), "Duplicate ward_id found"


# ===========================================================================
# Section 10 — WardService: coordinate lookup & list
# ===========================================================================


class TestWardServiceCoordinates:
    @pytest.mark.asyncio
    async def test_find_ward_by_coordinates_calls_ensure_seeded(self):
        db = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=result_mock)

        with patch.object(WardService, "ensure_seeded", new_callable=AsyncMock) as mock_seed:
            await WardService.find_ward_by_coordinates(db, 13.07, 80.26)

        mock_seed.assert_awaited_once_with(db)

    @pytest.mark.asyncio
    async def test_find_ward_by_coordinates_returns_ward_when_found(self):
        db = AsyncMock()
        ward = Ward(ward_id="ward_05_royapuram", ward_name="Royapuram Ward 50")
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = ward
        db.execute = AsyncMock(return_value=result_mock)

        with patch.object(WardService, "ensure_seeded", new_callable=AsyncMock):
            result = await WardService.find_ward_by_coordinates(db, 13.07, 80.26)

        assert result is ward

    @pytest.mark.asyncio
    async def test_find_ward_by_coordinates_returns_none_when_not_found(self):
        db = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=result_mock)

        with patch.object(WardService, "ensure_seeded", new_callable=AsyncMock):
            result = await WardService.find_ward_by_coordinates(db, 0.0, 0.0)

        assert result is None

    @pytest.mark.asyncio
    async def test_list_all_wards_calls_ensure_seeded(self):
        db = AsyncMock()
        scalars_mock = MagicMock()
        scalars_mock.all.return_value = []
        result_mock = MagicMock()
        result_mock.scalars.return_value = scalars_mock
        db.execute = AsyncMock(return_value=result_mock)

        with patch.object(WardService, "ensure_seeded", new_callable=AsyncMock) as mock_seed:
            await WardService.list_all_wards(db)

        mock_seed.assert_awaited_once_with(db)

    @pytest.mark.asyncio
    async def test_list_all_wards_returns_list_of_ward_objects(self):
        db = AsyncMock()
        w1 = Ward(ward_id="a", ward_name="Alpha")
        w2 = Ward(ward_id="b", ward_name="Beta")
        scalars_mock = MagicMock()
        scalars_mock.all.return_value = [w1, w2]
        result_mock = MagicMock()
        result_mock.scalars.return_value = scalars_mock
        db.execute = AsyncMock(return_value=result_mock)

        with patch.object(WardService, "ensure_seeded", new_callable=AsyncMock):
            result = await WardService.list_all_wards(db)

        assert result == [w1, w2]


# ===========================================================================
# Section 11 — WardService: get_ward_stats
# ===========================================================================


class TestWardServiceStats:
    def _scalar_mock(self, value: int) -> MagicMock:
        m = MagicMock()
        m.scalar.return_value = value
        return m

    @pytest.mark.asyncio
    async def test_all_zero_counts_produces_zero_resolution_rate(self):
        db = AsyncMock()
        z = self._scalar_mock(0)
        db.execute = AsyncMock(side_effect=[z, z, z])

        result = await WardService.get_ward_stats(db, "ward_x")

        assert result["resolution_rate"] == 0.0
        assert result["total_issues"] == 0

    @pytest.mark.asyncio
    async def test_only_resolved_issues_gives_100_percent_rate(self):
        db = AsyncMock()
        z = self._scalar_mock(0)
        r = self._scalar_mock(5)
        # open=0, resolved=5, rejected=0
        db.execute = AsyncMock(side_effect=[z, r, z])

        result = await WardService.get_ward_stats(db, "ward_y")

        assert result["resolution_rate"] == 100.0
        assert result["total_issues"] == 5
        assert result["resolved_issues"] == 5

    @pytest.mark.asyncio
    async def test_only_open_issues_gives_zero_resolution_rate(self):
        db = AsyncMock()
        o = self._scalar_mock(8)
        z = self._scalar_mock(0)
        # open=8, resolved=0, rejected=0
        db.execute = AsyncMock(side_effect=[o, z, z])

        result = await WardService.get_ward_stats(db, "ward_z")

        assert result["resolution_rate"] == 0.0
        assert result["open_issues"] == 8
        assert result["total_issues"] == 8

    @pytest.mark.asyncio
    async def test_mixed_counts_compute_rounded_resolution_rate(self):
        db = AsyncMock()
        # open=10, resolved=5, rejected=2  → total=17, rate=5/17*100 ≈ 29.41
        db.execute = AsyncMock(
            side_effect=[
                self._scalar_mock(10),
                self._scalar_mock(5),
                self._scalar_mock(2),
            ]
        )

        result = await WardService.get_ward_stats(db, "ward_05_royapuram")

        assert result["resolution_rate"] == round(5 / 17 * 100, 2)
        assert result["total_issues"] == 17
        assert result["rejected_issues"] == 2

    @pytest.mark.asyncio
    async def test_result_contains_all_expected_keys(self):
        db = AsyncMock()
        z = self._scalar_mock(0)
        db.execute = AsyncMock(side_effect=[z, z, z])

        result = await WardService.get_ward_stats(db, "w")

        for key in (
            "ward_id",
            "open_issues",
            "resolved_issues",
            "rejected_issues",
            "total_issues",
            "resolution_rate",
        ):
            assert key in result

    @pytest.mark.asyncio
    async def test_ward_id_is_echoed_verbatim_in_result(self):
        db = AsyncMock()
        z = self._scalar_mock(0)
        db.execute = AsyncMock(side_effect=[z, z, z])

        result = await WardService.get_ward_stats(db, "ward_13_adyar")

        assert result["ward_id"] == "ward_13_adyar"


# ===========================================================================
# Section 12 — DataRetentionScheduler
# ===========================================================================


@pytest.fixture
def session_factory_pair():
    """Returns (factory_mock, session_mock) with async context manager wired."""
    session = AsyncMock()
    factory = MagicMock()
    factory.return_value.__aenter__.return_value = session
    factory.return_value.__aexit__ = AsyncMock(return_value=None)
    return factory, session


class TestDataRetentionScheduler:
    def test_init_stores_factory_and_sets_idle_defaults(self, session_factory_pair):
        factory, _ = session_factory_pair
        sched = DataRetentionScheduler(factory)
        assert sched.session_factory is factory
        assert sched._running is False
        assert sched._task is None

    @pytest.mark.asyncio
    async def test_start_sets_running_true_and_creates_task(self, session_factory_pair):
        factory, _ = session_factory_pair
        sched = DataRetentionScheduler(factory)

        await sched.start(interval_seconds=86400)

        assert sched._running is True
        assert sched._task is not None
        sched.stop()  # cleanup

    @pytest.mark.asyncio
    async def test_start_second_call_is_noop_preserves_task_as_none(self, session_factory_pair):
        """Second start() while running=True must return early without creating a task."""
        factory, _ = session_factory_pair
        sched = DataRetentionScheduler(factory)
        sched._running = True  # simulate already started; _task is still None

        await sched.start()

        assert sched._task is None  # no new task created
        sched._running = False

    def test_stop_before_start_does_not_raise(self, session_factory_pair):
        factory, _ = session_factory_pair
        sched = DataRetentionScheduler(factory)
        sched.stop()  # _task is None — should not raise
        assert sched._running is False

    def test_stop_sets_running_false_and_cancels_task(self, session_factory_pair):
        factory, _ = session_factory_pair
        sched = DataRetentionScheduler(factory)
        mock_task = MagicMock()
        sched._running = True
        sched._task = mock_task

        sched.stop()

        assert sched._running is False
        mock_task.cancel.assert_called_once()

    def test_stop_when_no_task_only_clears_running(self, session_factory_pair):
        factory, _ = session_factory_pair
        sched = DataRetentionScheduler(factory)
        sched._running = True
        sched._task = None

        sched.stop()  # must not raise on None task

        assert sched._running is False

    @pytest.mark.asyncio
    async def test_cleanup_executes_stored_procedure_and_commits(self, session_factory_pair):
        factory, session = session_factory_pair
        session.execute = AsyncMock()
        session.commit = AsyncMock()
        sched = DataRetentionScheduler(factory)

        await sched.cleanup()

        session.execute.assert_awaited_once_with("SELECT safevixai_cleanup_expired_data()")
        session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_cleanup_rollback_on_db_exception(self, session_factory_pair):
        factory, session = session_factory_pair
        session.execute = AsyncMock(side_effect=RuntimeError("db exploded"))
        session.rollback = AsyncMock()
        sched = DataRetentionScheduler(factory)

        await sched.cleanup()

        session.rollback.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_loop_cancelled_error_breaks_cleanly(self, session_factory_pair):
        factory, _ = session_factory_pair
        sched = DataRetentionScheduler(factory)
        sched._running = True
        sched.cleanup = AsyncMock()

        with patch("asyncio.sleep", AsyncMock(side_effect=asyncio.CancelledError)):
            await sched._loop(1)

        sched.cleanup.assert_not_called()

    @pytest.mark.asyncio
    async def test_loop_exception_in_cleanup_continues_loop_not_breaks(self, session_factory_pair):
        """
        A non-CancelledError exception in cleanup() must be caught and the loop must
        continue to the next iteration — verifiable by counting sleep calls.

        Trace:
          Iteration 1: sleep (calls=1) → cleanup raises → except Exception → continue
          Iteration 2: sleep (calls=2, sets _running=False) → `if not running: break`
        """
        factory, _ = session_factory_pair
        sched = DataRetentionScheduler(factory)
        sched._running = True

        sleep_calls = 0

        async def controlled_sleep(_: int) -> None:
            nonlocal sleep_calls
            sleep_calls += 1
            if sleep_calls >= 2:
                sched._running = False

        cleanup_calls = 0

        async def failing_cleanup() -> None:
            nonlocal cleanup_calls
            cleanup_calls += 1
            raise RuntimeError("transient error")

        sched.cleanup = failing_cleanup

        with patch("asyncio.sleep", controlled_sleep):
            await sched._loop(1)

        # loop ran twice, proving exception path continued rather than broke
        assert sleep_calls == 2
        # cleanup was attempted once; second loop hit `if not running: break` before cleanup
        assert cleanup_calls == 1

    @pytest.mark.asyncio
    async def test_loop_stopped_during_sleep_skips_cleanup(self, session_factory_pair):
        """Setting _running=False inside sleep causes `if not self._running: break`."""
        factory, _ = session_factory_pair
        sched = DataRetentionScheduler(factory)
        sched._running = True
        sched.cleanup = AsyncMock()

        async def fake_sleep(_: int) -> None:
            sched._running = False

        with patch("asyncio.sleep", fake_sleep):
            await sched._loop(1)

        sched.cleanup.assert_not_called()
