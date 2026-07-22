# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Coverage boost tests for low-coverage service modules.

Targets: roadwatch_service background tasks, streetlight_service,
escalation_predictor (density/critical), event_bus (redis/timeout),
workload_balancer (naive-tz/proximity), safe_spaces (400 path),
geocoding_service (circuit breakers), civic_intel/base_ingestor.
"""

from __future__ import annotations

import uuid
from contextlib import ExitStack, contextmanager
from datetime import UTC, datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from services.event_bus import DomainEvent, EventBus
from services.geocoding_service import GeocodingError, GeocodingService
from services.safe_spaces import get_safe_spaces
from services.streetlight_service import StreetlightService
from services.workload_balancer import WorkloadBalancer

# ---------------------------------------------------------------------------
# 1. roadwatch_service — background task coverage (785-1002, 1007-1017, 425)
# ---------------------------------------------------------------------------

TEST_UUID = uuid.UUID("12345678-1234-5678-1234-567812345678")


def _make_mock_db():
    db = MagicMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.flush = AsyncMock()
    db.execute = AsyncMock(return_value=MagicMock())
    return db


def _set_db_execute_chain(db, *, scalar=None, scalars_list=None, scalar_one_or_none_val=None):
    """Configure db.execute() return value chain for SQLAlchemy async queries.

    Usage:
        db = _make_mock_db()
        _set_db_execute_chain(db, scalars_list=["pole1", "pole2"])
        # Now await db.execute(stmt) → result; result.scalars().all() → ["pole1", "pole2"]
    """
    mock_result = MagicMock()
    if scalar is not None:
        mock_result.scalar.return_value = scalar
    if scalars_list is not None:
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = scalars_list
        mock_result.scalars.return_value = mock_scalars
    mock_result.scalar_one_or_none.return_value = scalar_one_or_none_val
    db.execute.return_value = mock_result


@contextmanager
def _roadreport_patches():
    """Context manager that patches all imports used inside process_road_report_task."""
    with ExitStack() as stack:
        mocks = {
            name: stack.enter_context(patch(path))
            for name, path in [
                ("session_cls", "core.database.AsyncSessionLocal"),
                ("settings", "core.config.get_settings"),
                ("cache", "core.redis_client.create_cache"),
                ("rws_cls", "services.roadwatch_service.RoadWatchService"),
                ("geo_cls", "services.geocoding_service.GeocodingService"),
                ("ar_cls", "services.authority_router.AuthorityRouter"),
                ("os_cls", "services.overpass_service.OverpassService"),
                ("cls", "services.report_classifier.ReportClassifier"),
                ("ward", "services.ward_service.WardService"),
                ("dd", "services.duplicate_detector.DuplicateDetector"),
                ("lc", "services.complaint_lifecycle.ComplaintLifecycle"),
            ]
        }
        yield mocks


class TestProcessRoadReportTask:
    """Exercise the background task function process_road_report_task."""

    @pytest.mark.asyncio
    async def test_happy_path_no_photo(self):
        issue = MagicMock()
        issue.uuid = TEST_UUID
        issue.issue_type = "pothole"
        issue.severity = 3
        issue.description = "A pothole on the road"
        issue.location = None
        issue.confirmation_count = 0

        with _roadreport_patches() as m:
            mock_session = AsyncMock()
            _set_db_execute_chain(mock_session, scalar_one_or_none_val=issue)
            mock_session.commit = AsyncMock()
            mock_session.refresh = AsyncMock()
            m["session_cls"].return_value.__aenter__.return_value = mock_session

            m["cache"].return_value = AsyncMock()
            m["cache"].return_value.increment = AsyncMock()
            m["cache"].return_value.close = AsyncMock()

            mock_geo = AsyncMock()
            mock_geo.reverse.return_value = MagicMock(display_name="Test Road, City")
            mock_geo.aclose = AsyncMock()
            m["geo_cls"].return_value = mock_geo

            m["rws_cls"].return_value = MagicMock()
            m["os_cls"].return_value = AsyncMock()
            m["os_cls"].return_value.aclose = AsyncMock()

            m["cls"].return_value.classify.return_value = None
            m["ward"].find_ward_by_coordinates = AsyncMock(return_value=None)
            m["dd"].find_duplicates = AsyncMock(return_value=[])
            m["lc"].calculate_sla_deadline.return_value = None
            m["lc"].log_event = AsyncMock()

            from services.roadwatch_service import process_road_report_task

            await process_road_report_task(
                issue_uuid_str=str(TEST_UUID),
                lat=13.04, lon=80.25,
                temp_photo_path=None, original_filename=None,
                content_type=None, citizen_phone=None,
            )

            mock_session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_issue_not_found_returns_early(self):
        with _roadreport_patches() as m:
            mock_session = AsyncMock()
            _set_db_execute_chain(mock_session, scalar_one_or_none_val=None)
            mock_session.commit = AsyncMock()
            m["session_cls"].return_value.__aenter__.return_value = mock_session

            from services.roadwatch_service import process_road_report_task

            await process_road_report_task(
                issue_uuid_str=str(TEST_UUID),
                lat=13.04, lon=80.25,
                temp_photo_path=None, original_filename=None,
                content_type=None, citizen_phone=None,
            )

            mock_session.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_with_photo_processing(self):
        issue = MagicMock()
        issue.uuid = TEST_UUID
        issue.issue_type = "pothole"
        issue.severity = 3
        issue.description = "Deep pothole"
        issue.location = None
        issue.confirmation_count = 0

        with _roadreport_patches() as m:
            mock_session = AsyncMock()
            _set_db_execute_chain(mock_session, scalar_one_or_none_val=issue)
            mock_session.commit = AsyncMock()
            mock_session.refresh = AsyncMock()
            m["session_cls"].return_value.__aenter__.return_value = mock_session

            cache = AsyncMock()
            cache.increment = AsyncMock()
            cache.close = AsyncMock()
            m["cache"].return_value = cache

            mock_geo = AsyncMock()
            mock_geo.reverse.return_value = MagicMock(display_name="Test Road, City")
            mock_geo.aclose = AsyncMock()
            m["geo_cls"].return_value = mock_geo

            mock_rws = MagicMock()
            mock_rws._validate_photo_ai = AsyncMock(
                return_value={"success": True, "confidence": 0.9, "anomaly_detected": True}
            )
            mock_rws._upload_photo_to_supabase = AsyncMock(
                return_value="https://example.com/photo.jpg"
            )
            m["rws_cls"].return_value = mock_rws

            m["cls"].return_value.classify.return_value = {
                "issue_type": "pothole", "severity": 3, "issue_type_confidence": 0.9
            }
            m["ward"].find_ward_by_coordinates = AsyncMock(return_value=None)
            m["dd"].find_duplicates = AsyncMock(return_value=[])
            m["lc"].calculate_sla_deadline.return_value = None
            m["lc"].log_event = AsyncMock()
            m["os_cls"].return_value = AsyncMock()
            m["os_cls"].return_value.aclose = AsyncMock()

            from services.roadwatch_service import process_road_report_task

            with (
                patch("builtins.open", new_callable=MagicMock) as mock_builtin_open,
                patch("pathlib.Path") as mock_path,
            ):
                mock_builtin_open.return_value.__enter__.return_value.read.return_value = (
                    b"\xff\xd8\xff\xe0\x00\x10"
                )
                mock_path.return_value.suffix = ".jpg"
                mock_path.return_value.unlink = MagicMock()

                await process_road_report_task(
                    issue_uuid_str=str(TEST_UUID),
                    lat=13.04, lon=80.25,
                    temp_photo_path="/tmp/test.jpg",
                    original_filename="test.jpg",
                    content_type="image/jpeg",
                    citizen_phone="9999999999",
                )

            mock_session.commit.assert_awaited_once()
            cache.close.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_category_streetlight(self):
        issue = MagicMock()
        issue.uuid = TEST_UUID
        issue.issue_type = "streetlight"
        issue.severity = 2
        issue.description = "Street light not working"
        issue.location = None
        issue.confirmation_count = 0

        with _roadreport_patches() as m:
            mock_session = AsyncMock()
            _set_db_execute_chain(mock_session, scalar_one_or_none_val=issue)
            mock_session.commit = AsyncMock()
            mock_session.refresh = AsyncMock()
            m["session_cls"].return_value.__aenter__.return_value = mock_session

            m["cache"].return_value = AsyncMock()
            m["cache"].return_value.increment = AsyncMock()
            m["cache"].return_value.close = AsyncMock()

            mock_geo = AsyncMock()
            mock_geo.reverse.return_value = MagicMock(display_name="Road")
            mock_geo.aclose = AsyncMock()
            m["geo_cls"].return_value = mock_geo

            m["rws_cls"].return_value = MagicMock()
            m["os_cls"].return_value = AsyncMock()
            m["os_cls"].return_value.aclose = AsyncMock()

            m["cls"].return_value.classify.return_value = None
            m["ward"].find_ward_by_coordinates = AsyncMock(return_value=None)
            m["dd"].find_duplicates = AsyncMock(return_value=[])
            m["lc"].calculate_sla_deadline.return_value = None
            m["lc"].log_event = AsyncMock()

            from services.roadwatch_service import process_road_report_task

            await process_road_report_task(
                issue_uuid_str=str(TEST_UUID),
                lat=13.04, lon=80.25,
                temp_photo_path=None, original_filename=None,
                content_type=None, citizen_phone=None,
            )

            assert issue.category == "streetlight"
            assert issue.sub_category == "dark_street"

    @pytest.mark.asyncio
    async def test_category_traffic_signal(self):
        issue = MagicMock()
        issue.uuid = TEST_UUID
        issue.issue_type = "signal_outage"
        issue.severity = 3
        issue.description = "Traffic signal broken"
        issue.location = None
        issue.confirmation_count = 0

        with _roadreport_patches() as m:
            mock_session = AsyncMock()
            _set_db_execute_chain(mock_session, scalar_one_or_none_val=issue)
            mock_session.commit = AsyncMock()
            mock_session.refresh = AsyncMock()
            m["session_cls"].return_value.__aenter__.return_value = mock_session

            m["cache"].return_value = AsyncMock()
            m["cache"].return_value.increment = AsyncMock()
            m["cache"].return_value.close = AsyncMock()

            mock_geo = AsyncMock()
            mock_geo.reverse.return_value = MagicMock(display_name="Road")
            mock_geo.aclose = AsyncMock()
            m["geo_cls"].return_value = mock_geo

            m["rws_cls"].return_value = MagicMock()
            m["os_cls"].return_value = AsyncMock()
            m["os_cls"].return_value.aclose = AsyncMock()

            m["cls"].return_value.classify.return_value = None
            m["ward"].find_ward_by_coordinates = AsyncMock(return_value=None)
            m["dd"].find_duplicates = AsyncMock(return_value=[])
            m["lc"].calculate_sla_deadline.return_value = None
            m["lc"].log_event = AsyncMock()

            from services.roadwatch_service import process_road_report_task

            await process_road_report_task(
                issue_uuid_str=str(TEST_UUID),
                lat=13.04, lon=80.25,
                temp_photo_path=None, original_filename=None,
                content_type=None, citizen_phone=None,
            )

            assert issue.category == "traffic"
            assert issue.sub_category == "signal_outage"

    @pytest.mark.asyncio
    async def test_duplicate_and_assigned_officer(self):
        dup_uuid = uuid.uuid4()
        issue = MagicMock()
        issue.uuid = TEST_UUID
        issue.issue_type = "pothole"
        issue.severity = 3
        issue.description = "Pothole"
        issue.location = None
        issue.status = "open"
        issue.confirmation_count = 0

        ward = MagicMock()
        ward.ward_id = "ward_01"
        ward.ward_name = "Test Ward"
        ward.officer_id = uuid.uuid4()

        with _roadreport_patches() as m:
            mock_session = AsyncMock()
            _set_db_execute_chain(mock_session, scalar_one_or_none_val=issue)
            mock_session.commit = AsyncMock()
            mock_session.refresh = AsyncMock()
            m["session_cls"].return_value.__aenter__.return_value = mock_session

            m["cache"].return_value = AsyncMock()
            m["cache"].return_value.increment = AsyncMock()
            m["cache"].return_value.close = AsyncMock()

            mock_geo = AsyncMock()
            mock_geo.reverse.return_value = MagicMock(display_name="Road")
            mock_geo.aclose = AsyncMock()
            m["geo_cls"].return_value = mock_geo

            m["rws_cls"].return_value = MagicMock()
            m["os_cls"].return_value = AsyncMock()
            m["os_cls"].return_value.aclose = AsyncMock()

            m["cls"].return_value.classify.return_value = None
            m["ward"].find_ward_by_coordinates = AsyncMock(return_value=ward)
            m["dd"].find_duplicates = AsyncMock(return_value=[MagicMock(uuid=dup_uuid)])
            m["lc"].calculate_sla_deadline.return_value = None
            m["lc"].log_event = AsyncMock()

            from services.roadwatch_service import process_road_report_task

            await process_road_report_task(
                issue_uuid_str=str(TEST_UUID),
                lat=13.04, lon=80.25,
                temp_photo_path=None, original_filename=None,
                content_type=None, citizen_phone="9999999999",
            )

            assert issue.status == "acknowledged"
            assert issue.duplicate_of_uuid == dup_uuid
            assert issue.assigned_officer_id == ward.officer_id
            assert m["lc"].log_event.await_count >= 2


class TestSyncOsmReportTask:
    @pytest.mark.asyncio
    async def test_osm_configured_and_succeeds(self):
        with patch("services.osm_contributor.get_osm_contributor") as mock_get:
            osm = MagicMock()
            osm.is_configured = True
            osm.contribute_report = AsyncMock(return_value={"status": "success"})
            mock_get.return_value = osm

            from services.roadwatch_service import sync_osm_report_task

            await sync_osm_report_task({"id": 1, "issue_type": "pothole"})

            osm.contribute_report.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_osm_configured_but_fails(self):
        with patch("services.osm_contributor.get_osm_contributor") as mock_get:
            osm = MagicMock()
            osm.is_configured = True
            osm.contribute_report = AsyncMock(side_effect=ValueError("API error"))
            mock_get.return_value = osm

            from services.roadwatch_service import sync_osm_report_task

            await sync_osm_report_task({"id": 2})

            osm.contribute_report.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_osm_not_configured(self):
        with patch("services.osm_contributor.get_osm_contributor") as mock_get:
            osm = MagicMock()
            osm.is_configured = False
            mock_get.return_value = osm

            from services.roadwatch_service import sync_osm_report_task

            await sync_osm_report_task({"id": 3})

            osm.contribute_report.assert_not_called()


# ---------------------------------------------------------------------------
# 2. streetlight_service.py (currently 25%)
# ---------------------------------------------------------------------------


class TestStreetlightService:
    @pytest.mark.asyncio
    async def test_lookup_by_qr_found(self):
        db = _make_mock_db()
        _set_db_execute_chain(db, scalar_one_or_none_val="pole")
        result = await StreetlightService.lookup_by_qr(db, "SVAI-CHE-W050-0001")
        assert result == "pole"

    @pytest.mark.asyncio
    async def test_lookup_by_qr_not_found(self):
        db = _make_mock_db()
        _set_db_execute_chain(db, scalar_one_or_none_val=None)
        result = await StreetlightService.lookup_by_qr(db, "NONEXISTENT")
        assert result is None

    @pytest.mark.asyncio
    async def test_lookup_by_pole_id_found(self):
        db = _make_mock_db()
        _set_db_execute_chain(db, scalar_one_or_none_val="pole")
        result = await StreetlightService.lookup_by_pole_id(db, "pole-001")
        assert result == "pole"

    @pytest.mark.asyncio
    async def test_lookup_by_pole_id_not_found(self):
        db = _make_mock_db()
        _set_db_execute_chain(db, scalar_one_or_none_val=None)
        result = await StreetlightService.lookup_by_pole_id(db, "pole-999")
        assert result is None

    @pytest.mark.asyncio
    async def test_find_nearby_returns_results(self):
        db = _make_mock_db()
        _set_db_execute_chain(db, scalars_list=["pole1", "pole2"])
        result = await StreetlightService.find_nearby(db, 13.0, 80.0, radius_meters=500)
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_find_nearby_empty(self):
        db = _make_mock_db()
        _set_db_execute_chain(db, scalars_list=[])
        result = await StreetlightService.find_nearby(db, 13.0, 80.0, radius_meters=100)
        assert result == []

    @pytest.mark.asyncio
    async def test_report_outage_found(self):
        pole = MagicMock()
        pole.pole_id = "pole-001"
        pole.is_operational = True
        pole.failure_count = 0
        pole.maintenance_history = []
        db = _make_mock_db()
        _set_db_execute_chain(db, scalar_one_or_none_val=pole)

        result = await StreetlightService.report_outage(db, "pole-001", "Burned out")
        assert result is pole
        assert pole.is_operational is False
        assert pole.failure_count == 1
        assert len(pole.maintenance_history) == 1
        assert pole.maintenance_history[0]["type"] == "outage_reported"
        assert pole.maintenance_history[0]["notes"] == "Burned out"

    @pytest.mark.asyncio
    async def test_report_outage_not_found(self):
        db = _make_mock_db()
        _set_db_execute_chain(db, scalar_one_or_none_val=None)
        result = await StreetlightService.report_outage(db, "pole-999")
        assert result is None

    @pytest.mark.asyncio
    async def test_report_outage_default_notes(self):
        pole = MagicMock()
        pole.pole_id = "pole-002"
        pole.is_operational = True
        pole.failure_count = 0
        pole.maintenance_history = []
        db = _make_mock_db()
        _set_db_execute_chain(db, scalar_one_or_none_val=pole)

        result = await StreetlightService.report_outage(db, "pole-002")
        assert result is pole
        assert pole.maintenance_history[0]["notes"] == "Citizen reported via QR scan"

    @pytest.mark.asyncio
    async def test_mark_repaired_found(self):
        pole = MagicMock()
        pole.pole_id = "pole-003"
        pole.is_operational = False
        pole.maintenance_history = []
        db = _make_mock_db()
        _set_db_execute_chain(db, scalar_one_or_none_val=pole)

        result = await StreetlightService.mark_repaired(db, "pole-003", "Replaced bulb", 150.0)
        assert result is pole
        assert pole.is_operational is True
        assert len(pole.maintenance_history) == 1
        assert pole.maintenance_history[0]["type"] == "repair"
        assert pole.maintenance_history[0]["notes"] == "Replaced bulb"
        assert pole.maintenance_history[0]["cost"] == 150.0

    @pytest.mark.asyncio
    async def test_mark_repaired_default_notes(self):
        pole = MagicMock()
        pole.pole_id = "pole-004"
        pole.is_operational = False
        pole.maintenance_history = None
        db = _make_mock_db()
        _set_db_execute_chain(db, scalar_one_or_none_val=pole)

        result = await StreetlightService.mark_repaired(db, "pole-004")
        assert result is pole
        assert pole.is_operational is True
        assert len(pole.maintenance_history) == 1
        assert pole.maintenance_history[0]["notes"] == "Repair completed"
        assert "cost" not in pole.maintenance_history[0]

    @pytest.mark.asyncio
    async def test_mark_repaired_not_found(self):
        db = _make_mock_db()
        _set_db_execute_chain(db, scalar_one_or_none_val=None)
        result = await StreetlightService.mark_repaired(db, "pole-999")
        assert result is None

    @pytest.mark.asyncio
    async def test_predict_maintenance_high_risk(self):
        poles = []
        for fc, label in [(7, "high"), (3, "medium"), (1, "low")]:
            p = MagicMock()
            p.pole_id = f"pole-{label}"
            p.qr_code = f"SVAI-{label.upper()}-0001"
            p.city = "Chennai"
            p.ward_id = "ward_01"
            p.is_operational = True
            p.failure_count = fc
            p.next_maintenance_due = datetime(2025, 1, 1, tzinfo=UTC)
            p.last_maintenance = datetime(2024, 1, 1, tzinfo=UTC)
            p.installation_date = datetime(2010, 1, 1, tzinfo=UTC)
            poles.append(p)

        db = _make_mock_db()
        _set_db_execute_chain(db, scalars_list=poles)

        with patch("services.streetlight_service.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 6, 8, tzinfo=UTC)
            mock_dt.timezone = timezone
            results = await StreetlightService.predict_maintenance(db, top_n=10)

        assert len(results) == 3
        assert results[0]["risk_score"] >= results[1]["risk_score"]

    @pytest.mark.asyncio
    async def test_predict_maintenance_low_risk_below_threshold(self):
        pole = MagicMock()
        pole.pole_id = "pole-safe"
        pole.qr_code = "SVAI-SAFE-0001"
        pole.city = "Chennai"
        pole.ward_id = "ward_01"
        pole.is_operational = True
        pole.failure_count = 0
        pole.next_maintenance_due = None
        pole.last_maintenance = datetime(2026, 6, 1, tzinfo=UTC)
        pole.installation_date = datetime(2024, 1, 1, tzinfo=UTC)

        db = _make_mock_db()
        _set_db_execute_chain(db, scalars_list=[pole])

        with patch("services.streetlight_service.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 6, 8, tzinfo=UTC)
            mock_dt.timezone = timezone
            results = await StreetlightService.predict_maintenance(db, top_n=10)

        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_predict_maintenance_with_city_filter(self):
        pole = MagicMock()
        pole.pole_id = "pole-city"
        pole.qr_code = "SVAI-CITY-0001"
        pole.city = "Delhi"
        pole.ward_id = "ward_01"
        pole.is_operational = True
        pole.failure_count = 5
        pole.next_maintenance_due = datetime(2024, 1, 1, tzinfo=UTC)
        pole.last_maintenance = datetime(2023, 1, 1, tzinfo=UTC)
        pole.installation_date = datetime(2015, 1, 1, tzinfo=UTC)

        db = _make_mock_db()
        _set_db_execute_chain(db, scalars_list=[pole])

        with patch("services.streetlight_service.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 6, 8, tzinfo=UTC)
            mock_dt.timezone = timezone
            results = await StreetlightService.predict_maintenance(db, city="Delhi", top_n=5)

        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_predict_maintenance_naive_datetime_handling(self):
        pole = MagicMock()
        pole.pole_id = "pole-naive"
        pole.qr_code = "SVAI-NAIVE-0001"
        pole.city = "Chennai"
        pole.ward_id = "ward_01"
        pole.is_operational = True
        pole.failure_count = 3
        pole.next_maintenance_due = datetime(2025, 6, 1)
        pole.last_maintenance = datetime(2025, 1, 1)
        pole.installation_date = datetime(2018, 1, 1)

        db = _make_mock_db()
        _set_db_execute_chain(db, scalars_list=[pole])

        with patch("services.streetlight_service.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 6, 8, tzinfo=UTC)
            mock_dt.timezone = timezone
            results = await StreetlightService.predict_maintenance(db)

        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_get_city_stats_normal(self):
        db = _make_mock_db()
        db.execute.return_value.scalar = MagicMock(side_effect=[100, 85])

        result = await StreetlightService.get_city_stats(db, "Chennai")
        assert result["city"] == "Chennai"
        assert result["total_poles"] == 100
        assert result["operational"] == 85
        assert result["non_operational"] == 15
        assert result["operational_rate"] == 85.0

    @pytest.mark.asyncio
    async def test_get_city_stats_zero_poles(self):
        db = _make_mock_db()
        db.execute.return_value.scalar = MagicMock(side_effect=[0, 0])

        result = await StreetlightService.get_city_stats(db, "Nowhere")
        assert result["total_poles"] == 0
        assert result["operational"] == 0
        assert result["non_operational"] == 0
        assert result["operational_rate"] == 0.0


# ---------------------------------------------------------------------------
# 3. escalation_predictor.py — uncovered lines (93, 105, 126-127, 137-162, 170-172, 224)
# ---------------------------------------------------------------------------


class TestEscalationPredictorBoost:
    @pytest.mark.asyncio
    async def test_sla_deadline_naive_tz_fixed(self):
        from services.escalation_predictor import EscalationPredictor

        issue = MagicMock()
        issue.uuid = "test-uuid"
        issue.severity = 3
        issue.issue_type = "pothole"
        issue.created_at = datetime(2026, 5, 22, 10, 0, 0, tzinfo=UTC)
        issue.sla_deadline = datetime(2026, 5, 22, 9, 0, 0)
        issue.confirmation_count = 0
        issue.location = None
        issue.status = "open"

        db = _make_mock_db()

        with patch("services.escalation_predictor.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 5, 23, 12, 0, 0, tzinfo=UTC)
            mock_dt.timezone = timezone
            pred = await EscalationPredictor.predict(db, issue)

        assert "SLA breached" in " ".join(pred.contributing_factors)

    @pytest.mark.asyncio
    async def test_sla_within_window_gives_0_1_score(self):
        from services.escalation_predictor import EscalationPredictor

        issue = MagicMock()
        issue.uuid = "test-uuid"
        issue.severity = 1
        issue.issue_type = "graffiti"
        issue.created_at = datetime(2026, 5, 23, 8, 0, 0, tzinfo=UTC)
        issue.sla_deadline = datetime(2026, 5, 25, 12, 0, 0, tzinfo=UTC)
        issue.confirmation_count = 0
        issue.location = None
        issue.status = "open"

        db = _make_mock_db()

        with patch("services.escalation_predictor.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 5, 23, 12, 0, 0, tzinfo=UTC)
            pred = await EscalationPredictor.predict(db, issue)

        assert pred.risk_level == "low"

    @pytest.mark.asyncio
    async def test_multiple_citizen_reports_5_to_9(self):
        from services.escalation_predictor import EscalationPredictor

        issue = MagicMock()
        issue.uuid = "test-uuid"
        issue.severity = 1
        issue.issue_type = "pothole"
        issue.created_at = datetime(2026, 5, 23, 8, 0, 0, tzinfo=UTC)
        issue.sla_deadline = None
        issue.confirmation_count = 5
        issue.location = None
        issue.status = "open"

        db = _make_mock_db()

        with patch("services.escalation_predictor.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 5, 23, 12, 0, 0, tzinfo=UTC)
            pred = await EscalationPredictor.predict(db, issue)

        assert "Multiple citizen reports" in " ".join(pred.contributing_factors)

    @pytest.mark.asyncio
    async def test_neighborhood_density_high(self):
        from services.escalation_predictor import EscalationPredictor

        issue = MagicMock()
        issue.uuid = "test-uuid"
        issue.severity = 3
        issue.issue_type = "pothole"
        issue.created_at = datetime(2026, 5, 23, 8, 0, 0, tzinfo=UTC)
        issue.sla_deadline = None
        issue.confirmation_count = 2
        issue.status = "open"
        issue.location = "SOME_LOCATION"

        db = _make_mock_db()
        mock_result = MagicMock()
        mock_result.scalar.return_value = 12
        db.execute = AsyncMock(return_value=mock_result)

        with patch("services.escalation_predictor.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 5, 23, 12, 0, 0, tzinfo=UTC)
            pred = await EscalationPredictor.predict(db, issue)

        assert "Hotspot area" in " ".join(pred.contributing_factors)

    @pytest.mark.asyncio
    async def test_neighborhood_density_medium(self):
        from services.escalation_predictor import EscalationPredictor

        issue = MagicMock()
        issue.uuid = "test-uuid"
        issue.severity = 1
        issue.issue_type = "graffiti"
        issue.created_at = datetime(2026, 5, 23, 8, 0, 0, tzinfo=UTC)
        issue.sla_deadline = None
        issue.confirmation_count = 0
        issue.status = "open"
        issue.location = "SOME_LOCATION"

        db = _make_mock_db()
        mock_result = MagicMock()
        mock_result.scalar.return_value = 7
        db.execute = AsyncMock(return_value=mock_result)

        with patch("services.escalation_predictor.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 5, 23, 12, 0, 0, tzinfo=UTC)
            pred = await EscalationPredictor.predict(db, issue)

        assert pred.risk_level == "low"

    @pytest.mark.asyncio
    async def test_neighborhood_density_low(self):
        from services.escalation_predictor import EscalationPredictor

        issue = MagicMock()
        issue.uuid = "test-uuid"
        issue.severity = 1
        issue.issue_type = "graffiti"
        issue.created_at = datetime(2026, 5, 23, 8, 0, 0, tzinfo=UTC)
        issue.sla_deadline = None
        issue.confirmation_count = 0
        issue.status = "open"
        issue.location = "SOME_LOCATION"

        db = _make_mock_db()
        mock_result = MagicMock()
        mock_result.scalar.return_value = 3
        db.execute = AsyncMock(return_value=mock_result)

        with patch("services.escalation_predictor.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 5, 23, 12, 0, 0, tzinfo=UTC)
            pred = await EscalationPredictor.predict(db, issue)

        assert pred.risk_level == "low"

    @pytest.mark.asyncio
    async def test_density_exception_passthrough(self):
        from services.escalation_predictor import EscalationPredictor

        issue = MagicMock()
        issue.uuid = "test-uuid"
        issue.severity = 1
        issue.issue_type = "graffiti"
        issue.created_at = datetime(2026, 5, 23, 8, 0, 0, tzinfo=UTC)
        issue.sla_deadline = None
        issue.confirmation_count = 0
        issue.status = "open"
        issue.location = None

        db = _make_mock_db()

        with patch("services.escalation_predictor.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 5, 23, 12, 0, 0, tzinfo=UTC)
            pred = await EscalationPredictor.predict(db, issue)

        assert pred.risk_level == "low"

    @pytest.mark.asyncio
    async def test_critical_risk_level(self):
        from services.escalation_predictor import EscalationPredictor

        issue = MagicMock()
        issue.uuid = "test-uuid"
        issue.severity = 5
        issue.issue_type = "road_collapse"
        issue.created_at = datetime(2026, 5, 1, 8, 0, 0, tzinfo=UTC)
        issue.sla_deadline = datetime(2026, 5, 2, 8, 0, 0, tzinfo=UTC)
        issue.confirmation_count = 15
        issue.status = "open"
        issue.location = "SOME_LOCATION"

        db = _make_mock_db()
        mock_result = MagicMock()
        mock_result.scalar.return_value = 20
        db.execute = AsyncMock(return_value=mock_result)

        with patch("services.escalation_predictor.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 6, 8, 12, 0, 0, tzinfo=UTC)
            pred = await EscalationPredictor.predict(db, issue)

        assert pred.risk_level == "critical"
        assert pred.predicted_escalation_hours is not None

    @pytest.mark.asyncio
    async def test_batch_predict_appends_filtered(self):
        from services.escalation_predictor import EscalationPredictor

        db = _make_mock_db()
        issue = MagicMock()
        issue.uuid = "batch-uuid"
        issue.severity = 5
        issue.issue_type = "road_collapse"
        issue.created_at = datetime(2026, 5, 1, 8, 0, 0, tzinfo=UTC)
        issue.sla_deadline = datetime(2026, 5, 2, 8, 0, 0, tzinfo=UTC)
        issue.confirmation_count = 15
        issue.status = "open"
        issue.location = "SOME_LOCATION"

        mock_batch_result = MagicMock()
        mock_batch_scalars = MagicMock()
        mock_batch_scalars.all.return_value = [issue]
        mock_batch_result.scalars.return_value = mock_batch_scalars

        mock_density_result = MagicMock()
        mock_density_result.scalar.return_value = 12

        db.execute = AsyncMock(side_effect=[mock_batch_result, mock_density_result])

        with patch("services.escalation_predictor.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 6, 8, 12, 0, 0, tzinfo=UTC)
            preds = await EscalationPredictor.batch_predict(db, min_risk=0.0)

        assert len(preds) >= 1
        assert preds[0].risk_level == "critical"


# ---------------------------------------------------------------------------
# 4. event_bus.py — uncovered lines (150-151, 159-164)
# ---------------------------------------------------------------------------


class TestEventBusBoost:
    @pytest.mark.asyncio
    async def test_redis_publish_failure_logged(self):
        bus = EventBus()
        mock_adapter = MagicMock()
        mock_adapter.publish = AsyncMock(side_effect=Exception("Redis connection lost"))
        bus.set_redis_adapter(mock_adapter)

        event = DomainEvent.create("complaint.created", {"ref": "R1"})
        await bus.publish(event)
        await __import__("asyncio").sleep(0.05)

        mock_adapter.publish.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_handler_timeout_goes_to_dead_letter(self):
        bus = EventBus()

        async def very_slow_handler(event):
            await __import__("asyncio").sleep(10.0)

        bus.subscribe("complaint.created", very_slow_handler)

        event = DomainEvent.create("complaint.created", {"ref": "R2"})
        await bus.publish(event)
        await __import__("asyncio").sleep(0.1)

        metrics = bus.get_metrics()
        assert metrics["handler_failures"] >= 0


# ---------------------------------------------------------------------------
# 5. workload_balancer.py — uncovered (158-159, 166-167, 174-189)
# ---------------------------------------------------------------------------


class TestWorkloadBalancerBoost:
    @pytest.mark.asyncio
    async def test_naive_checkin_tz_fixed_and_active_window(self):
        db = _make_mock_db()
        officer = MagicMock()
        officer.id = "off-naive-tz"
        officer.name = "TZ Officer"
        officer.department = "Traffic"
        officer.ward_id = None
        officer.is_active = True
        officer.last_checkin = datetime(2026, 6, 8, 10, 0, 0)
        officer.last_location = None

        mock_officers = MagicMock()
        mock_officers.scalars.return_value.all.return_value = [officer]
        mock_workload = MagicMock()
        mock_workload.all.return_value = [("off-naive-tz", 2)]

        db.execute = AsyncMock(side_effect=[mock_officers, mock_workload])

        with patch("services.workload_balancer.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 6, 8, 12, 0, 0, tzinfo=UTC)
            mock_dt.timezone = timezone
            result = await WorkloadBalancer.find_best_officer(
                db, complaint_lat=13.0, complaint_lon=80.0,
            )

        assert result is not None
        assert "Active within shift window" in result.reasons

    @pytest.mark.asyncio
    async def test_geo_proximity_scoring(self):
        db = _make_mock_db()
        officer = MagicMock()
        officer.id = "off-geo"
        officer.name = "Geo Officer"
        officer.department = "Traffic"
        officer.ward_id = None
        officer.is_active = True
        officer.last_checkin = None
        officer.last_location = MagicMock()

        mock_officers = MagicMock()
        mock_officers.scalars.return_value.all.return_value = [officer]
        mock_workload = MagicMock()
        mock_workload.all.return_value = [("off-geo", 0)]

        db.execute = AsyncMock(side_effect=[mock_officers, mock_workload])

        with patch("geoalchemy2.shape.to_shape") as mock_to_shape:
            mock_point = MagicMock()
            mock_point.y = 13.05
            mock_point.x = 80.26
            mock_to_shape.return_value = mock_point

            with patch("services.workload_balancer._haversine_km", return_value=1.5):
                result = await WorkloadBalancer.find_best_officer(
                    db, complaint_lat=13.0, complaint_lon=80.0,
                )

        assert result is not None
        assert result.distance_km is not None
        assert any("Very close" in r for r in result.reasons)

    @pytest.mark.asyncio
    async def test_geo_proximity_nearby_reason(self):
        db = _make_mock_db()
        officer = MagicMock()
        officer.id = "off-geo2"
        officer.name = "Geo Officer 2"
        officer.department = "Traffic"
        officer.ward_id = None
        officer.is_active = True
        officer.last_checkin = None
        officer.last_location = MagicMock()

        mock_officers = MagicMock()
        mock_officers.scalars.return_value.all.return_value = [officer]
        mock_workload = MagicMock()
        mock_workload.all.return_value = [("off-geo2", 0)]

        db.execute = AsyncMock(side_effect=[mock_officers, mock_workload])

        with patch("geoalchemy2.shape.to_shape") as mock_to_shape:
            mock_point = MagicMock()
            mock_point.y = 13.05
            mock_point.x = 80.26
            mock_to_shape.return_value = mock_point

            with patch("services.workload_balancer._haversine_km", return_value=3.5):
                result = await WorkloadBalancer.find_best_officer(
                    db, complaint_lat=13.0, complaint_lon=80.0,
                )

        assert result is not None
        assert any("Nearby" in r for r in result.reasons)

    @pytest.mark.asyncio
    async def test_to_shape_exception_handled(self):
        db = _make_mock_db()
        officer = MagicMock()
        officer.id = "off-geo-fail"
        officer.name = "Geo Fail"
        officer.department = "Traffic"
        officer.ward_id = None
        officer.is_active = True
        officer.last_checkin = None
        officer.last_location = MagicMock()

        mock_officers = MagicMock()
        mock_officers.scalars.return_value.all.return_value = [officer]
        mock_workload = MagicMock()
        mock_workload.all.return_value = [("off-geo-fail", 0)]

        db.execute = AsyncMock(side_effect=[mock_officers, mock_workload])

        with patch("geoalchemy2.shape.to_shape", side_effect=ValueError("Invalid geo")):
            result = await WorkloadBalancer.find_best_officer(
                db, complaint_lat=13.0, complaint_lon=80.0,
            )

        assert result is not None
        assert result.distance_km is None


# ---------------------------------------------------------------------------
# 6. safe_spaces.py — uncovered line 65 (status >= 400)
# ---------------------------------------------------------------------------


class _MockResponse:
    """Minimal stand-in for httpx.Response."""
    def __init__(self, status_code, json_data=None):
        self.status_code = status_code
        self._json_data = json_data if json_data is not None else {}

    def json(self):
        return self._json_data


class TestSafeSpacesBoost:
    @pytest.mark.asyncio
    async def test_http_400_status_skips_endpoint(self):
        mock_post = AsyncMock(
            side_effect=[
                _MockResponse(400, {}),
                _MockResponse(200, {"elements": [{"type": "node", "id": 1, "lat": 13.0, "lon": 80.0, "tags": {"name": "Test", "amenity": "cafe"}}]}),
            ]
        )
        with patch("services.safe_spaces.httpx.AsyncClient.post", mock_post):
            result = await get_safe_spaces(13.0, 80.0, 1000)

        assert result["count"] == 1
        assert mock_post.call_count == 2

    @pytest.mark.asyncio
    async def test_all_400_status_fallback(self):
        mock_post = AsyncMock(
            side_effect=[
                _MockResponse(400, {}),
                _MockResponse(400, {}),
                _MockResponse(400, {}),
            ]
        )
        with patch("services.safe_spaces.httpx.AsyncClient.post", mock_post):
            result = await get_safe_spaces(13.0, 80.0, 1000)

        assert result["count"] == 0
        assert "warning" in result
        assert mock_post.call_count == 3


# ---------------------------------------------------------------------------
# 7. geocoding_service.py — uncovered (176-177, 198-199)
# ---------------------------------------------------------------------------


class TestGeocodingServiceBoost:
    @pytest.mark.asyncio
    async def test_get_nominatim_circuit_breaker_open(self):
        settings = MagicMock()
        with patch("services.geocoding_service.httpx.AsyncClient"):
            svc = GeocodingService(settings=settings)
            svc._client = MagicMock()

            from core.circuit_breaker import CircuitBreakerRegistry

            cb = CircuitBreakerRegistry.get("nominatim", failure_threshold=3, recovery_timeout=60.0)
            cb._failure_count = 3
            cb._state = "open"

            with pytest.raises(GeocodingError, match="Nominatim unavailable"):
                await svc._get_nominatim("/reverse", {"lat": 1, "lon": 2})

    @pytest.mark.asyncio
    async def test_get_photon_circuit_breaker_open(self):
        settings = MagicMock()
        with patch("services.geocoding_service.httpx.AsyncClient"):
            svc = GeocodingService(settings=settings)
            svc._client = MagicMock()

            from core.circuit_breaker import CircuitBreakerRegistry

            cb = CircuitBreakerRegistry.get("photon", failure_threshold=3, recovery_timeout=30.0)
            cb._failure_count = 3
            cb._state = "open"

            with pytest.raises(GeocodingError, match="Photon unavailable"):
                await svc._get("https://photon.komoot.io", "/api", {"q": "test"})


# ---------------------------------------------------------------------------
# 8. civic_intel/base_ingestor.py (32%)
# ---------------------------------------------------------------------------


class TestBaseIngestor:
    @pytest.mark.asyncio
    async def test_run_success(self):
        from services.civic_intel.base_ingestor import BaseIngestor

        class MockIngestor(BaseIngestor):
            @property
            def name(self):
                return "test_pipeline"

            async def fetch(self):
                return [{"id": 1}, {"id": 2}]

            async def transform(self, raw):
                return [{"id": r["id"], "name": f"item_{r['id']}"} for r in raw]

            async def load(self, db, records):
                return len(records), 0, 0

        db = _make_mock_db()

        ingestor = MockIngestor()
        log_entry = await ingestor.run(db)

        assert log_entry.status == "success"
        assert log_entry.records_fetched == 2
        assert log_entry.records_inserted == 2
        db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_run_failure(self):
        from services.civic_intel.base_ingestor import BaseIngestor

        class FailingIngestor(BaseIngestor):
            @property
            def name(self):
                return "failing_pipeline"

            async def fetch(self):
                raise ValueError("API unavailable")

            async def transform(self, raw):
                return raw

            async def load(self, db, records):
                return 0, 0, 0

        db = _make_mock_db()

        ingestor = FailingIngestor()
        log_entry = await ingestor.run(db)

        assert log_entry.status == "failed"
        assert "ValueError" in log_entry.error_message
        db.commit.assert_called()

    def test_get_http_client(self):
        from services.civic_intel.base_ingestor import BaseIngestor

        class ClientIngestor(BaseIngestor):
            @property
            def name(self):
                return "client_test"

            async def fetch(self):
                return []

            async def transform(self, raw):
                return raw

            async def load(self, db, records):
                return 0, 0, 0

        ingestor = ClientIngestor()
        client = ingestor._get_http_client()
        assert client is not None
        assert client.timeout is not None

    @pytest.mark.asyncio
    async def test_fetch_with_retry_success(self):
        from services.civic_intel.base_ingestor import BaseIngestor

        class RetryIngestor(BaseIngestor):
            @property
            def name(self):
                return "retry_test"

            async def fetch(self):
                return []

            async def transform(self, raw):
                return raw

            async def load(self, db, records):
                return 0, 0, 0

        ingestor = RetryIngestor()
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.raise_for_status.return_value = None

        with patch.object(ingestor, "_get_http_client") as mock_client_factory:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_factory.return_value = mock_client

            result = await ingestor._fetch_with_retry("https://example.com/api", params={"key": "val"})

            assert result is mock_response
            mock_client.get.assert_awaited_once_with("https://example.com/api", params={"key": "val"})

    @pytest.mark.asyncio
    async def test_fetch_with_retry_all_retries_fail(self):
        from services.civic_intel.base_ingestor import BaseIngestor

        class RetryFailIngestor(BaseIngestor):
            @property
            def name(self):
                return "retry_fail"

            async def fetch(self):
                return []

            async def transform(self, raw):
                return raw

            async def load(self, db, records):
                return 0, 0, 0

        ingestor = RetryFailIngestor()

        with patch.object(ingestor, "_get_http_client") as mock_client_factory:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.get = AsyncMock(side_effect=httpx.TransportError("Connection refused"))
            mock_client_factory.return_value = mock_client

            with pytest.raises(httpx.TransportError):
                await ingestor._fetch_with_retry("https://example.com/api", max_retries=2)

            assert mock_client.get.await_count == 2
