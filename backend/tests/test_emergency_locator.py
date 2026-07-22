# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

import math
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from core.config import Settings
from core.redis_client import CacheHelper
from models.emergency import EmergencyService
from models.schemas import (
    EmergencyNumber,
    EmergencyResponse,
    EmergencyServiceItem,
    SosResponse,
)
from services.emergency_locator import (
    CITY_CENTERS,
    DEFAULT_EMERGENCY_NUMBERS_DATA,
    EMERGENCY_NUMBERS,
    OFFLINE_CITY_CENTERS,
    SUPPORTED_CATEGORIES,
    EmergencyLocatorService,
    _load_emergency_numbers,
)
from services.exceptions import ExternalServiceError, ServiceValidationError
from services.local_emergency_catalog import LocalEmergencyEntry
from services.overpass_service import OverpassService

# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_service_item(
    id: str = "1",
    name: str = "Test Hospital",
    category: str = "hospital",
    sub_category: str | None = "general",
    phone: str | None = "1234567890",
    phone_emergency: str | None = "108",
    lat: float = 13.0827,
    lon: float = 80.2707,
    distance_meters: float = 500.0,
    has_trauma: bool = False,
    has_icu: bool = False,
    is_24hr: bool = True,
    address: str | None = "Test Address",
    source: str = "database",
) -> EmergencyServiceItem:
    return EmergencyServiceItem(
        id=id, name=name, category=category, sub_category=sub_category,
        phone=phone, phone_emergency=phone_emergency, lat=lat, lon=lon,
        distance_meters=distance_meters, has_trauma=has_trauma, has_icu=has_icu,
        is_24hr=is_24hr, address=address, source=source,
    )


def _db_mock(scalar_return: int = 5, rows: list | None = None) -> AsyncMock:
    db = AsyncMock()
    db.execute = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar.return_value = scalar_return
    mock_result.all.return_value = rows or []
    db.execute.return_value = mock_result
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    db.close = AsyncMock()
    return db


def _db_mock_with_rows(items: list[EmergencyServiceItem], total: int = 5) -> AsyncMock:
    db = AsyncMock()
    db.execute = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar.return_value = total
    rows = []
    for item in items:
        svc = MagicMock(spec=EmergencyService)
        svc.id = int(item.id) if item.id.isdigit() else hash(item.id) % 10**6
        svc.name = item.name
        svc.category = item.category
        svc.sub_category = item.sub_category
        svc.phone = item.phone
        svc.phone_emergency = item.phone_emergency
        svc.has_trauma = item.has_trauma
        svc.has_icu = item.has_icu
        svc.is_24hr = item.is_24hr
        svc.address = item.address
        svc.source = item.source
        rows.append((svc, item.lat, item.lon, item.distance_meters))
    mock_result.all.return_value = rows
    db.execute.return_value = mock_result
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    db.close = AsyncMock()
    return db


def _count_sql_objects(calls: list) -> tuple[list, list]:
    count_sqls = []
    select_sqls = []
    for call in calls:
        sql = str(call[0][0])
        if "count(" in sql.lower():
            count_sqls.append(sql)
        else:
            select_sqls.append(sql)
    return count_sqls, select_sqls


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def settings() -> Settings:
    return Settings()


@pytest.fixture
def cache() -> AsyncMock:
    c = AsyncMock(spec=CacheHelper)
    c.get_json.return_value = None
    return c


@pytest.fixture
def overpass_service() -> AsyncMock:
    s = AsyncMock(spec=OverpassService)
    s.search_services.return_value = []
    return s


@pytest.fixture
def service(settings: Settings, cache: AsyncMock, overpass_service: AsyncMock) -> EmergencyLocatorService:
    return EmergencyLocatorService(settings=settings, cache=cache, overpass_service=overpass_service)


# ── _load_emergency_numbers / EMERGENCY_NUMBERS ──────────────────────────────


class TestEmergencyNumbersModule:
    def test_emergency_numbers_contains_112(self):
        assert EMERGENCY_NUMBERS.numbers["national_emergency"].service == "112"

    def test_emergency_numbers_contains_102(self):
        assert EMERGENCY_NUMBERS.numbers["ambulance"].service == "102"

    def test_emergency_numbers_contains_100(self):
        assert EMERGENCY_NUMBERS.numbers["police"].service == "100"

    def test_emergency_numbers_contains_1033(self):
        all_services = {num.service for num in EMERGENCY_NUMBERS.numbers.values()}
        assert "1033" in all_services

    def test_emergency_numbers_schema_valid(self):
        for key, num in EMERGENCY_NUMBERS.numbers.items():
            assert isinstance(num, EmergencyNumber), f"{key} is not an EmergencyNumber"
            assert isinstance(num.service, str) and num.service, f"{key}.service is empty"
            assert isinstance(num.coverage, str) and num.coverage, f"{key}.coverage is empty"

    def test_load_emergency_numbers_returns_default_when_file_missing(self):
        with patch("services.emergency_locator.Path.exists", return_value=False):
            result = _load_emergency_numbers()
        assert result.numbers["national_emergency"].service == "112"

    def test_load_emergency_numbers_uses_file_when_present(self):
        fake_json = (
            '{"numbers": {"test_helpline": {"service": "199", "coverage": "Test", "notes": "test"}}}'
        )
        with (
            patch("services.emergency_locator.Path.exists", return_value=True),
            patch("services.emergency_locator.Path.read_text", return_value=fake_json),
        ):
            result = _load_emergency_numbers()
        assert result.numbers["test_helpline"].service == "199"

    def test_load_emergency_numbers_fallback_on_invalid_json(self):
        with (
            patch("services.emergency_locator.Path.exists", return_value=True),
            patch("services.emergency_locator.Path.read_text", return_value="not valid json {{{"),
        ):
            result = _load_emergency_numbers()
        assert result.numbers["national_emergency"].service == "112"

    def test_load_emergency_numbers_fallback_on_non_dict(self):
        with (
            patch("services.emergency_locator.Path.exists", return_value=True),
            patch("services.emergency_locator.Path.read_text", return_value='"just a string"'),
        ):
            result = _load_emergency_numbers()
        assert result.numbers["national_emergency"].service == "112"

    def test_load_emergency_numbers_fallback_when_missing_numbers_key(self):
        with (
            patch("services.emergency_locator.Path.exists", return_value=True),
            patch("services.emergency_locator.Path.read_text", return_value='{"other": "data"}'),
        ):
            result = _load_emergency_numbers()
        assert result.numbers["national_emergency"].service == "112"

    def test_load_emergency_numbers_filters_empty_service(self):
        with (
            patch("services.emergency_locator.Path.exists", return_value=True),
            patch("services.emergency_locator.Path.read_text",
                  return_value='{"numbers": {"empty": {"service": "", "coverage": ""}}}'),
        ):
            result = _load_emergency_numbers()
        assert "empty" not in result.numbers

    def test_load_emergency_numbers_OError_fallback(self):
        with (
            patch("services.emergency_locator.Path.exists", return_value=True),
            patch("services.emergency_locator.Path.read_text", side_effect=OSError("denied")),
        ):
            result = _load_emergency_numbers()
        assert result.numbers["national_emergency"].service == "112"

    def test_default_data_road_accident_1033(self):
        assert DEFAULT_EMERGENCY_NUMBERS_DATA["road_accident"]["service"] == "1033"


# ── __init__ ──────────────────────────────────────────────────────────────────


class TestInit:
    def test_init_sets_attributes(self, service, settings, cache, overpass_service):
        assert service.settings is settings
        assert service.cache is cache
        assert service.overpass_service is overpass_service
        assert service._local_catalog is None

    def test_init_creates_independent_instances(self, settings, cache, overpass_service):
        s1 = EmergencyLocatorService(settings=settings, cache=cache, overpass_service=overpass_service)
        s2 = EmergencyLocatorService(settings=settings, cache=cache, overpass_service=overpass_service)
        assert s1 is not s2


# ── parse_categories ─────────────────────────────────────────────────────────


class TestParseCategories:
    def test_default(self, service):
        assert service.parse_categories(None) == ["hospital", "police", "ambulance", "towing"]

    def test_comma_separated(self, service):
        assert service.parse_categories("hospital, police, fire") == ["hospital", "police", "fire"]

    def test_iterable(self, service):
        assert service.parse_categories(["hospital", "fire"]) == ["hospital", "fire"]

    def test_unsupported_filtered(self, service):
        assert service.parse_categories(["hospital", "unknown", "fire"]) == ["hospital", "fire"]

    def test_all_unsupported_returns_defaults(self, service):
        assert service.parse_categories(["magic", "unicorn"]) == ["hospital", "police", "ambulance", "towing"]

    def test_empty_string(self, service):
        assert service.parse_categories("") == ["hospital", "police", "ambulance", "towing"]

    def test_empty_list(self, service):
        assert service.parse_categories([]) == ["hospital", "police", "ambulance", "towing"]

    def test_normalizes_case(self, service):
        assert service.parse_categories("Hospital, POLICE") == ["hospital", "police"]

    def test_all_supported(self, service):
        result = service.parse_categories(list(SUPPORTED_CATEGORIES))
        assert sorted(result) == sorted(SUPPORTED_CATEGORIES)

    def test_single_item(self, service):
        assert service.parse_categories("fire") == ["fire"]

    def test_iterable_single(self, service):
        assert service.parse_categories(["fire"]) == ["fire"]


# ── build_radius_steps ───────────────────────────────────────────────────────


class TestBuildRadiusSteps:
    def test_default(self, service):
        assert service.build_radius_steps(None) == list(service.settings.emergency_radius_steps)

    def test_capped(self, service):
        result = service.build_radius_steps(999999)
        assert result[-1] == service.settings.max_radius

    def test_filters_above(self, service):
        result = service.build_radius_steps(5000)
        assert all(s <= 5000 for s in result)
        assert result[-1] == 5000

    def test_appends_capped(self, service):
        result = service.build_radius_steps(7500)
        assert result[-1] == 7500

    def test_uses_exact_step(self, service):
        assert service.build_radius_steps(5000).count(5000) == 1

    def test_below_smallest_step(self, service):
        assert service.build_radius_steps(200) == [200]

    def test_converts_int_and_includes_intermediate_steps(self, service):
        result = service.build_radius_steps(5000.7)
        assert isinstance(result[-1], int)
        assert result[-1] == 5000
        assert result == [500, 1000, 5000]


# ── find_nearby ───────────────────────────────────────────────────────────────


class TestFindNearby:
    async def test_cached(self, service, cache):
        cached_data = {
            "services": [], "count": 0, "radius_used": 5000,
            "source": "database", "next_offset": None, "total_count": 0,
        }
        cache.get_json.return_value = cached_data
        db = _db_mock()

        result = await service.find_nearby(db=db, lat=13.08, lon=80.27, categories=None)

        assert isinstance(result, EmergencyResponse)
        assert result.count == 0
        assert result.radius_used == 5000
        cache.get_json.assert_awaited_once()
        cache.set_json.assert_not_awaited()

    @patch.object(EmergencyLocatorService, "_search_local_catalog", return_value=[])
    async def test_cache_miss(self, mock_local, service, cache, overpass_service):
        cache.get_json.return_value = None
        db = _db_mock(scalar_return=3)
        overpass_service.search_services.return_value = []

        result = await service.find_nearby(db=db, lat=13.08, lon=80.27, categories=None)

        assert isinstance(result, EmergencyResponse)
        assert result.radius_used == 50000
        cache.set_json.assert_awaited_once()

    @patch.object(EmergencyLocatorService, "_search_local_catalog", return_value=[])
    async def test_passes_arguments(self, mock_local, service, cache, overpass_service):
        cache.get_json.return_value = None
        db = _db_mock(scalar_return=0)
        overpass_service.search_services.return_value = []

        result = await service.find_nearby(
            db=db, lat=13.08, lon=80.27, categories="fire,police", radius=10000, limit=5, offset=10,
        )

        assert result.radius_used == 10000

    @patch.object(EmergencyLocatorService, "_search_local_catalog", return_value=[])
    async def test_external_service_error(self, mock_local, service, cache, overpass_service):
        cache.get_json.return_value = None
        cache.get_json_stale.return_value = None
        db = _db_mock(scalar_return=0)
        overpass_service.search_services.side_effect = ExternalServiceError("Overpass down")

        with pytest.raises(ExternalServiceError, match="Overpass down"):
            await service.find_nearby(db=db, lat=13.08, lon=80.27, categories=None)

    @patch.object(EmergencyLocatorService, "_search_local_catalog", return_value=[])
    async def test_empty_results(self, mock_local, service, cache, overpass_service):
        cache.get_json.return_value = None
        db = _db_mock(scalar_return=0)
        overpass_service.search_services.return_value = []

        result = await service.find_nearby(db=db, lat=13.08, lon=80.27, categories=None)

        assert result.count == 0
        assert result.services == []

    @patch.object(EmergencyLocatorService, "_search_local_catalog", return_value=[])
    async def test_unsupported_category(self, mock_local, service, cache, overpass_service):
        cache.get_json.return_value = None
        db = _db_mock(scalar_return=0)
        overpass_service.search_services.return_value = []

        result = await service.find_nearby(db=db, lat=13.08, lon=80.27, categories="unknown,invalid")

        assert result.services == []

    async def test_overpass_fallback_swallows_error_when_db_has_results(self, service, cache, overpass_service):
        cache.get_json.return_value = None
        items = [_make_service_item(id="1", name="DB Hospital", source="database")]
        db = _db_mock_with_rows(items, total=1)
        overpass_service.search_services.side_effect = ExternalServiceError("Overpass down")

        with patch.object(service, "_search_local_catalog", return_value=[]):
            result = await service.find_nearby(db=db, lat=13.08, lon=80.27, categories=None)

        assert result.count >= 1
        assert result.services[0].name == "DB Hospital"

    @patch.object(EmergencyLocatorService, "_search_local_catalog", return_value=[])
    async def test_sql_contains_postgis(self, mock_local, service, cache):
        cache.get_json.return_value = None
        db = _db_mock(scalar_return=0)

        await service.find_nearby(db=db, lat=13.08, lon=80.27, categories=["hospital"], radius=5000)

        statements_seen = set()
        for call in db.execute.await_args_list:
            sql = str(call[0][0])
            statements_seen.add("ST_DWithin" if "ST_DWithin" in sql else "other")

        assert "ST_DWithin" in statements_seen

    @patch.object(EmergencyLocatorService, "_search_local_catalog", return_value=[])
    async def test_with_overpass_results(self, mock_local, service, cache, overpass_service):
        cache.get_json.return_value = None
        db = _db_mock(scalar_return=0)
        op_item = _make_service_item(id="op-1", name="Overpass Facility", source="overpass")
        overpass_service.search_services.return_value = [op_item]

        result = await service.find_nearby(db=db, lat=13.08, lon=80.27, categories=None)

        assert result.count == 1
        assert result.source == "overpass"
        assert result.services[0].name == "Overpass Facility"

    async def test_local_results_without_overpass(self, service, cache, overpass_service):
        cache.get_json.return_value = None
        db = _db_mock(scalar_return=0)
        overpass_service.search_services.return_value = []

        local_items = [
            _make_service_item(id="local-1", name="Local Clinic", source="local_csv"),
            _make_service_item(id="local-2", name="Local Pharmacy", source="local_csv"),
            _make_service_item(id="local-3", name="Local Hospital", source="local_csv"),
        ]
        with patch.object(service, "_search_local_catalog", return_value=local_items):
            result = await service.find_nearby(db=db, lat=13.08, lon=80.27, categories=None)

        assert result.count >= 3
        assert result.source == "local"

    @patch.object(EmergencyLocatorService, "_search_local_catalog", return_value=[])
    async def test_combines_db_local_overpass(self, mock_local, service, cache, overpass_service):
        cache.get_json.return_value = None
        db = _db_mock(scalar_return=0)
        overpass_service.search_services.return_value = [
            _make_service_item(id="op-1", name="Overpass", source="overpass"),
        ]

        with patch.object(service, "_search_local_catalog", return_value=[
            _make_service_item(id="local-1", name="Local", source="local_csv"),
        ]):
            result = await service.find_nearby(db=db, lat=13.08, lon=80.27, categories=None)

        assert result.count == 2

    @patch.object(EmergencyLocatorService, "_search_local_catalog", return_value=[])
    async def test_next_offset(self, mock_local, service, cache, overpass_service):
        cache.get_json.return_value = None
        db = _db_mock(scalar_return=25)
        overpass_service.search_services.return_value = []

        result = await service.find_nearby(db=db, lat=13.08, lon=80.27, categories=None, limit=20, offset=0)

        assert result.next_offset == 20


# ── build_sos_payload ─────────────────────────────────────────────────────────


class TestBuildSosPayload:
    @patch.object(EmergencyLocatorService, "_search_local_catalog", return_value=[])
    async def test_returns_sos_response_with_numbers(self, mock_local, service, cache, overpass_service):
        cache.get_json.return_value = None
        db = _db_mock(scalar_return=0)
        overpass_service.search_services.return_value = []

        result = await service.build_sos_payload(db=db, lat=13.08, lon=80.27)

        assert isinstance(result, SosResponse)
        assert result.numbers is not None
        assert "112" in {num.service for num in result.numbers.values()}

    @patch.object(EmergencyLocatorService, "_search_local_catalog", return_value=[])
    async def test_with_overpass_services(self, mock_local, service, cache, overpass_service):
        cache.get_json.return_value = None
        db = _db_mock(scalar_return=0)
        overpass_service.search_services.return_value = [
            _make_service_item(id="h-1", name="AIIMS", category="hospital", source="overpass"),
        ]

        result = await service.build_sos_payload(db=db, lat=13.08, lon=80.27)

        assert result.count >= 1
        assert result.services[0].name == "AIIMS"

    @patch.object(EmergencyLocatorService, "_search_local_catalog", return_value=[])
    async def test_includes_all_essential_numbers(self, mock_local, service, cache, overpass_service):
        cache.get_json.return_value = None
        db = _db_mock(scalar_return=0)
        overpass_service.search_services.return_value = []

        result = await service.build_sos_payload(db=db, lat=13.08, lon=80.27)

        services = {num.service for num in result.numbers.values()}
        assert "112" in services
        assert "102" in services
        assert "100" in services
        assert "101" in services

    @patch.object(EmergencyLocatorService, "_search_local_catalog", return_value=[])
    async def test_empty_nearby_still_has_numbers(self, mock_local, service, cache, overpass_service):
        cache.get_json.return_value = None
        db = _db_mock(scalar_return=0)
        overpass_service.search_services.return_value = []

        result = await service.build_sos_payload(db=db, lat=13.08, lon=80.27)

        assert "112" in {num.service for num in result.numbers.values()}

    async def test_external_error(self, service, cache):
        cache.get_json.return_value = None
        cache.get_json_stale.return_value = None
        db = _db_mock(scalar_return=0)
        db.execute.side_effect = ExternalServiceError("Upstream timeout")

        with pytest.raises(ExternalServiceError, match="Upstream timeout"):
            await service.build_sos_payload(db=db, lat=13.08, lon=80.27)

    @patch.object(EmergencyLocatorService, "_search_local_catalog", return_value=[])
    async def test_uses_hospital_police_ambulance_categories(self, mock_local, service, cache, overpass_service):
        cache.get_json.return_value = None
        db = _db_mock(scalar_return=0)
        overpass_service.search_services.return_value = []

        await service.build_sos_payload(db=db, lat=13.08, lon=80.27)

        # Verify overpass was called with hospital/police/ambulance categories
        overpass_call = overpass_service.search_services.await_args
        assert overpass_call is not None
        kwargs = overpass_call[1]
        assert "hospital" in kwargs.get("categories", [])
        assert "police" in kwargs.get("categories", [])
        assert "ambulance" in kwargs.get("categories", [])


# ── build_city_bundle ─────────────────────────────────────────────────────────


class TestBuildCityBundle:
    @patch.object(EmergencyLocatorService, "_search_local_catalog", return_value=[])
    async def test_exact_match(self, mock_local, service, cache, overpass_service):
        cache.get_json.return_value = None
        db = _db_mock(scalar_return=0)
        overpass_service.search_services.return_value = []

        bundle = await service.build_city_bundle(db=db, city="Chennai")

        assert bundle["city"] == "Chennai"
        assert bundle["center"] == {"lat": 13.0827, "lon": 80.2707}
        assert bundle["source"] == "database"
        assert "numbers" in bundle
        assert bundle["services"] == []
        cache.set_json.assert_awaited_once()

    async def test_cached(self, service, cache):
        cached = {
            "city": "Chennai", "center": {"lat": 13.0827, "lon": 80.2707},
            "services": [], "numbers": {}, "source": "database",
        }
        cache.get_json.return_value = cached
        db = _db_mock()

        bundle = await service.build_city_bundle(db=db, city="Chennai")

        assert bundle == cached
        assert db.execute.await_count == 0

    async def test_unknown_city(self, service, cache):
        cache.get_json.return_value = None
        db = _db_mock()

        with pytest.raises(ServiceValidationError, match="Unknown offline bundle city"):
            await service.build_city_bundle(db=db, city="Atlantis")

    @patch.object(EmergencyLocatorService, "_search_local_catalog", return_value=[])
    async def test_case_insensitive(self, mock_local, service, cache, overpass_service):
        cache.get_json.return_value = None
        db = _db_mock(scalar_return=0)
        overpass_service.search_services.return_value = []

        bundle = await service.build_city_bundle(db=db, city="CHENNAI")
        assert bundle["city"] == "CHENNAI"
        assert bundle["center"]["lat"] == 13.0827

    @patch.object(EmergencyLocatorService, "_search_local_catalog", return_value=[])
    async def test_overpass_fallback(self, mock_local, service, cache, overpass_service):
        cache.get_json.return_value = None
        db = _db_mock(scalar_return=0)
        overpass_service.search_services.return_value = [
            _make_service_item(id="op-1", name="Overpass Hospital", source="overpass"),
        ]

        bundle = await service.build_city_bundle(db=db, city="Chennai")

        assert bundle["source"] == "overpass"
        assert len(bundle["services"]) == 1
        assert bundle["services"][0]["name"] == "Overpass Hospital"

    @patch.object(EmergencyLocatorService, "_search_local_catalog", return_value=[])
    async def test_overpass_error_silenced(self, mock_local, service, cache, overpass_service):
        cache.get_json.return_value = None
        db = _db_mock(scalar_return=0)
        overpass_service.search_services.side_effect = ExternalServiceError("Overpass down")

        bundle = await service.build_city_bundle(db=db, city="Chennai")

        assert bundle["source"] == "database"
        assert bundle["services"] == []


# ── _query_database ───────────────────────────────────────────────────────────


class TestQueryDatabase:
    async def test_executes_count_and_select(self, service):
        db = _db_mock(scalar_return=5)

        items, total = await service._query_database(
            db=db, lat=13.08, lon=80.27, categories=["hospital"], radius_meters=5000, limit=20,
        )

        assert total == 5
        assert db.execute.await_count >= 2
        count_sqls, select_sqls = _count_sql_objects(db.execute.await_args_list)
        assert len(count_sqls) >= 1
        assert len(select_sqls) >= 1

    async def test_returns_empty(self, service):
        db = _db_mock(scalar_return=0)

        items, total = await service._query_database(
            db=db, lat=13.08, lon=80.27, categories=["hospital"], radius_meters=5000, limit=20,
        )

        assert total == 0
        assert items == []

    async def test_generates_postgis(self, service):
        db = _db_mock(scalar_return=0)

        await service._query_database(
            db=db, lat=13.08, lon=80.27, categories=["hospital"], radius_meters=5000, limit=20,
        )

        found_make_point = False
        found_dwithin = False
        for call in db.execute.await_args_list:
            sql = str(call[0][0])
            if "ST_MakePoint" in sql:
                found_make_point = True
            if "ST_DWithin" in sql:
                found_dwithin = True
        assert found_make_point
        assert found_dwithin

    async def test_single_category(self, service):
        db = _db_mock(scalar_return=3)

        items, total = await service._query_database(
            db=db, lat=13.08, lon=80.27, categories=["fire"], radius_meters=10000, limit=10,
        )

        assert total == 3

    async def test_multiple_categories(self, service):
        db = _db_mock(scalar_return=8)

        items, total = await service._query_database(
            db=db, lat=13.08, lon=80.27, categories=["hospital", "police"], radius_meters=5000, limit=20,
        )

        assert total == 8

    async def test_applies_offset(self, service):
        db = _db_mock(scalar_return=10)

        await service._query_database(
            db=db, lat=13.08, lon=80.27, categories=["hospital"], radius_meters=5000, limit=5, offset=10,
        )

        count_sqls, select_sqls = _count_sql_objects(db.execute.await_args_list)
        # COUNT query should NOT have OFFSET, SELECT should
        for count_sql in count_sqls:
            assert ".offset(" not in count_sql and "OFFSET" not in count_sql
        for select_sql in select_sqls:
            assert ".offset(" in select_sql or "OFFSET " in select_sql


# ── _search_local_catalog / _get_local_catalog ────────────────────────────────


class TestLocalCatalog:
    def test_lazy_loads(self, service):
        assert service._local_catalog is None
        catalog = service._get_local_catalog()
        assert isinstance(catalog, list)
        assert service._local_catalog is not None

    def test_caches(self, service):
        c1 = service._get_local_catalog()
        c2 = service._get_local_catalog()
        assert c1 is c2

    def test_returns_matching_items(self, service):
        entries = [
            LocalEmergencyEntry(id="a", name="Local Hospital", category="hospital", lat=13.08, lon=80.27, phone="111", source="local_csv"),
            LocalEmergencyEntry(id="b", name="Local Police", category="police", lat=13.09, lon=80.28, phone="222", source="local_csv"),
            LocalEmergencyEntry(id="c", name="Far Fire", category="fire", lat=14.0, lon=81.0, phone="333", source="local_csv"),
        ]
        with patch.object(service, "_get_local_catalog", return_value=entries):
            items = service._search_local_catalog(
                lat=13.08, lon=80.27, categories=["hospital", "police"], radius_meters=50000, limit=10,
            )
        assert len(items) == 2
        assert items[0].name == "Local Hospital"
        assert items[1].name == "Local Police"

    def test_filters_by_category(self, service):
        entries = [
            LocalEmergencyEntry(id="f1", name="Fire", category="fire", lat=13.08, lon=80.27, source="local_csv"),
            LocalEmergencyEntry(id="h1", name="Hospital", category="hospital", lat=13.08, lon=80.27, source="local_csv"),
        ]
        with patch.object(service, "_get_local_catalog", return_value=entries):
            items = service._search_local_catalog(
                lat=13.08, lon=80.27, categories=["hospital"], radius_meters=50000, limit=10,
            )
        assert len(items) == 1
        assert items[0].name == "Hospital"

    def test_filters_by_radius(self, service):
        entries = [
            LocalEmergencyEntry(id="near", name="Nearby", category="hospital", lat=13.08, lon=80.27, source="local_csv"),
            LocalEmergencyEntry(id="far", name="Far", category="hospital", lat=14.0, lon=81.0, source="local_csv"),
        ]
        with patch.object(service, "_get_local_catalog", return_value=entries):
            items = service._search_local_catalog(
                lat=13.08, lon=80.27, categories=["hospital"], radius_meters=1000, limit=10,
            )
        assert len(items) == 1
        assert items[0].id == "near"

    def test_empty_catalog(self, service):
        with patch.object(service, "_get_local_catalog", return_value=[]):
            items = service._search_local_catalog(
                lat=13.08, lon=80.27, categories=["hospital"], radius_meters=50000, limit=10,
            )
        assert items == []

    def test_respects_limit(self, service):
        entries = [LocalEmergencyEntry(
            id=f"h{i}", name=f"Hospital {i}", category="hospital",
            lat=13.08 + i * 0.001, lon=80.27 + i * 0.001, source="local_csv",
        ) for i in range(20)]
        with patch.object(service, "_get_local_catalog", return_value=entries):
            items = service._search_local_catalog(
                lat=13.08, lon=80.27, categories=["hospital"], radius_meters=50000, limit=5,
            )
        assert len(items) == 5

    def test_sorted_by_trauma_then_24hr_then_distance(self, service):
        entries = [
            LocalEmergencyEntry(id="d", name="D", category="hospital", lat=13.09, lon=80.28, has_trauma=False, is_24hr=True, source="local_csv"),
            LocalEmergencyEntry(id="c", name="C", category="hospital", lat=13.08, lon=80.27, has_trauma=False, is_24hr=False, source="local_csv"),
            LocalEmergencyEntry(id="a", name="A", category="hospital", lat=13.082, lon=80.272, has_trauma=True, is_24hr=True, source="local_csv"),
            LocalEmergencyEntry(id="b", name="B", category="hospital", lat=13.081, lon=80.271, has_trauma=False, is_24hr=True, source="local_csv"),
        ]
        with patch.object(service, "_get_local_catalog", return_value=entries):
            items = service._search_local_catalog(
                lat=13.08, lon=80.27, categories=["hospital"], radius_meters=50000, limit=10,
            )
        assert len(items) == 4
        assert [item.id for item in items] == ["a", "b", "d", "c"]


# ── _entry_to_service_item ────────────────────────────────────────────────────


class TestEntryToServiceItem:
    def test_converts_fully(self, service):
        entry = LocalEmergencyEntry(
            id="test-1", name="Test Entry", category="hospital", sub_category="general",
            phone="12345", phone_emergency="108", lat=13.0, lon=80.0, address="Addr",
            has_trauma=True, has_icu=False, is_24hr=True, source="local_csv",
        )
        item = service._entry_to_service_item(entry, distance_meters=1500.0)
        assert isinstance(item, EmergencyServiceItem)
        assert item.id == "test-1"
        assert item.name == "Test Entry"
        assert item.category == "hospital"
        assert item.distance_meters == 1500.0
        assert item.has_trauma is True
        assert item.source == "local_csv"

    def test_converts_minimal(self, service):
        entry = LocalEmergencyEntry(id="test-2", name="Basic", category="police", lat=13.0, lon=80.0, source="local_csv")
        item = service._entry_to_service_item(entry, distance_meters=500.0)
        assert item.phone is None
        assert item.sub_category is None
        assert item.address is None


# ── _distance_meters ──────────────────────────────────────────────────────────


class TestDistanceMeters:
    def test_identical_points(self, service):
        assert service._distance_meters(13.0827, 80.2707, 13.0827, 80.2707) == 0.0

    def test_known_distance(self, service):
        d = service._distance_meters(13.0827, 80.2707, 13.0900, 80.2707)
        assert 800 < d < 1200

    def test_symmetric(self, service):
        a = service._distance_meters(12.0, 77.0, 13.0, 80.0)
        b = service._distance_meters(13.0, 80.0, 12.0, 77.0)
        assert abs(a - b) < 1.0

    def test_chennai_to_delhi(self, service):
        d = service._distance_meters(13.0827, 80.2707, 28.6139, 77.2090)
        assert 1700 < d / 1000 < 1900

    def test_antipodal(self, service):
        d = service._distance_meters(0, 0, 0, 180)
        assert 19000 < d / 1000 < 21000

    def test_chennai_to_bengaluru(self, service):
        d = service._distance_meters(13.0827, 80.2707, 12.9716, 77.5946)
        assert 270 < d / 1000 < 310


# ── _merge_results ────────────────────────────────────────────────────────────


class TestMergeResults:
    def test_deduplicates(self, service):
        db = [_make_service_item(id="1", name="Hospital", lat=13.08, lon=80.27)]
        op = [
            _make_service_item(id="2", name="Hospital", lat=13.08, lon=80.27),
            _make_service_item(id="3", name="Pharmacy", lat=13.09, lon=80.28),
        ]
        merged = service._merge_results(db, op, limit=10)
        assert len(merged) == 2
        assert {it.name for it in merged} == {"Hospital", "Pharmacy"}

    def test_respects_limit(self, service):
        db = [_make_service_item(id=str(i), name=f"DB-{i}") for i in range(3)]
        op = [_make_service_item(id=str(10 + i), name=f"OP-{i}") for i in range(10)]
        assert len(service._merge_results(db, op, limit=5)) == 5

    def test_sorts_by_trauma_then_24hr_then_distance(self, service):
        db = [
            _make_service_item(id="a", name="A", has_trauma=False, is_24hr=False, distance_meters=500),
            _make_service_item(id="b", name="B", has_trauma=True, is_24hr=True, distance_meters=1000),
        ]
        merged = service._merge_results(db, [], limit=10)
        assert [it.name for it in merged] == ["B", "A"]

    def test_empty_db(self, service):
        assert len(service._merge_results([], [_make_service_item(id="1", name="OP Only")], limit=10)) == 1

    def test_empty_both(self, service):
        assert service._merge_results([], [], limit=10) == []

    def test_deduplicates_rounded_location(self, service):
        db = [_make_service_item(id="1", name="Hospital", lat=13.08271, lon=80.27069)]
        op = [_make_service_item(id="2", name="Hospital", lat=13.08270, lon=80.27070)]
        assert len(service._merge_results(db, op, limit=10)) == 1

    def test_case_insensitive_name(self, service):
        db = [_make_service_item(id="1", name="Hospital")]
        op = [_make_service_item(id="2", name="hospital")]
        assert len(service._merge_results(db, op, limit=10)) == 1


# ── CITY_CENTERS / discover_city ──────────────────────────────────────────────


class TestDiscoverCity:
    def test_exact_match_chennai(self):
        assert CITY_CENTERS["chennai"] == (13.0827, 80.2707)

    def test_exact_match_delhi(self):
        assert CITY_CENTERS["delhi"] == (28.6139, 77.2090)

    def test_exact_match_mumbai(self):
        assert CITY_CENTERS["mumbai"] == (19.0760, 72.8777)

    def test_all_valid_coords(self):
        for name, (lat, lon) in CITY_CENTERS.items():
            assert -90 <= lat <= 90, f"{name}: lat {lat}"
            assert -180 <= lon <= 180, f"{name}: lon {lon}"

    def test_lowercase_keys(self):
        for key in CITY_CENTERS:
            assert key == key.lower()

    def test_offline_superset_includes_defaults(self):
        offline = set(OFFLINE_CITY_CENTERS.keys())
        for city in ("chennai", "bengaluru", "mumbai", "delhi", "kolkata"):
            assert city in offline

    def test_all_within_india(self):
        for name, (lat, lon) in CITY_CENTERS.items():
            assert 6.0 <= lat <= 36.0, f"{name}: lat {lat}"
            assert 68.0 <= lon <= 98.0, f"{name}: lon {lon}"

    def test_no_duplicates(self):
        assert len(CITY_CENTERS) == len(set(CITY_CENTERS.keys()))

    def test_nearest_city_chennai(self):
        def dist(lat1, lon1, lat2, lon2):
            R = 6371000
            phi1, phi2 = math.radians(lat1), math.radians(lat2)
            dphi = math.radians(lat2 - lat1)
            dlam = math.radians(lon2 - lon1)
            a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
            return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        nearest = min(CITY_CENTERS, key=lambda c: dist(13.08, 80.27, CITY_CENTERS[c][0], CITY_CENTERS[c][1]))
        assert nearest == "chennai"

    def test_nearest_city_coimbatore(self):
        def dist(lat1, lon1, lat2, lon2):
            R = 6371000
            phi1, phi2 = math.radians(lat1), math.radians(lat2)
            dphi = math.radians(lat2 - lat1)
            dlam = math.radians(lon2 - lon1)
            a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
            return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        nearest = min(CITY_CENTERS, key=lambda c: dist(11.02, 76.96, CITY_CENTERS[c][0], CITY_CENTERS[c][1]))
        assert nearest == "coimbatore"

    def test_ocean_far_from_any_city(self):
        def dist(lat1, lon1, lat2, lon2):
            R = 6371000
            phi1, phi2 = math.radians(lat1), math.radians(lat2)
            dphi = math.radians(lat2 - lat1)
            dlam = math.radians(lon2 - lon1)
            a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
            return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        nearest = min(CITY_CENTERS, key=lambda c: dist(0.0, -30.0, CITY_CENTERS[c][0], CITY_CENTERS[c][1]))
        nearest_km = dist(0.0, -30.0, CITY_CENTERS[nearest][0], CITY_CENTERS[nearest][1]) / 1000
        assert nearest_km > 5000

    def test_offline_matches_city_centers(self):
        for key in OFFLINE_CITY_CENTERS:
            assert key in CITY_CENTERS
            assert OFFLINE_CITY_CENTERS[key] == CITY_CENTERS[key]


# ── get_nearby_facilities (MCP helper) ────────────────────────────────────────


class TestGetNearbyFacilities:
    async def test_returns_items(self, service, overpass_service):
        overpass_service.search_services.return_value = [
            _make_service_item(id="op-1", name="OP Hospital", source="overpass"),
        ]
        with (
            patch.object(service, "_search_local_catalog", return_value=[]),
            patch.object(service, "_query_healthsites", return_value=[]),
        ):
            result = await service.get_nearby_facilities(lat=13.08, lon=80.27)
        assert len(result) == 1
        assert "confidence" in result[0].source

    async def test_expands_radius(self, service, overpass_service):
        overpass_service.search_services.side_effect = [
            [_make_service_item(id="1", name="A", source="overpass")],
            [_make_service_item(id="2", name="B", source="overpass")],
            [_make_service_item(id="3", name="C", source="overpass"), _make_service_item(id="4", name="D", source="overpass")],
        ]
        with (
            patch.object(service, "_search_local_catalog", return_value=[]),
            patch.object(service, "_query_healthsites", return_value=[]),
        ):
            result = await service.get_nearby_facilities(lat=13.08, lon=80.27)
        assert len(result) == 2
        assert overpass_service.search_services.await_count == 3

    async def test_stops_early_when_enough(self, service, overpass_service):
        items = [_make_service_item(id=str(i), name=f"F{i}", source="overpass") for i in range(5)]
        overpass_service.search_services.return_value = items
        with (
            patch.object(service, "_search_local_catalog", return_value=[]),
            patch.object(service, "_query_healthsites", return_value=[]),
        ):
            result = await service.get_nearby_facilities(lat=13.08, lon=80.27)
        assert len(result) >= 5
        overpass_service.search_services.assert_awaited_once()

    async def test_overpass_error_returns_empty(self, service, overpass_service):
        overpass_service.search_services.side_effect = ExternalServiceError("Overpass down")
        with (
            patch.object(service, "_search_local_catalog", return_value=[]),
            patch.object(service, "_query_healthsites", return_value=[]),
        ):
            result = await service.get_nearby_facilities(lat=13.08, lon=80.27)
        assert result == []

    async def test_combines_local_and_overpass(self, service, overpass_service):
        overpass_service.search_services.return_value = [
            _make_service_item(id="op-1", name="OP Hospital", source="overpass"),
        ]
        with (
            patch.object(service, "_search_local_catalog", return_value=[
                _make_service_item(id="local-1", name="Local Clinic", source="local_csv"),
            ]),
            patch.object(service, "_query_healthsites", return_value=[]),
        ):
            result = await service.get_nearby_facilities(lat=13.08, lon=80.27)
        assert len(result) == 2

    async def test_healthsites_fallback(self, service, overpass_service):
        overpass_service.search_services.return_value = [
            _make_service_item(id="1", name="Only Hospital", source="overpass"),
        ]
        with (
            patch.object(service, "_search_local_catalog", return_value=[]),
            patch.object(service, "_query_healthsites", return_value=[
                _make_service_item(id="hs-1", name="Healthsite Hospital", source="healthsites.io"),
            ]),
        ):
            result = await service.get_nearby_facilities(lat=13.08, lon=80.27)
        assert len(result) == 2

    async def test_confidence_high(self, service, overpass_service):
        overpass_service.search_services.return_value = [
            _make_service_item(id=str(i), name=f"F{i}", source="overpass") for i in range(5)
        ]
        with (
            patch.object(service, "_search_local_catalog", return_value=[]),
            patch.object(service, "_query_healthsites", return_value=[]),
        ):
            result = await service.get_nearby_facilities(lat=13.08, lon=80.27)
        assert "confidence:high" in result[0].source

    async def test_confidence_low(self, service, overpass_service):
        overpass_service.search_services.return_value = [
            _make_service_item(id="1", name="A", source="overpass"),
        ]
        with (
            patch.object(service, "_search_local_catalog", return_value=[]),
            patch.object(service, "_query_healthsites", return_value=[]),
        ):
            result = await service.get_nearby_facilities(lat=13.08, lon=80.27)
        assert len(result) == 1
        assert "confidence:low" in result[0].source

    async def test_healthsites_skipped_when_enough(self, service, overpass_service):
        overpass_service.search_services.return_value = [
            _make_service_item(id=str(i), name=f"F{i}", source="overpass") for i in range(5)
        ]
        with (
            patch.object(service, "_search_local_catalog", return_value=[]),
            patch.object(service, "_query_healthsites", return_value=[]),
        ):
            result = await service.get_nearby_facilities(lat=13.08, lon=80.27)
        assert len(result) >= 5


# ── SosResponse schema ────────────────────────────────────────────────────────


class TestSosResponseSchema:
    def test_all_fields(self):
        payload = SosResponse(
            services=[_make_service_item()], count=1, radius_used=5000,
            source="database", numbers=EMERGENCY_NUMBERS.numbers,
        )
        assert payload.count == 1
        assert payload.radius_used == 5000
        assert payload.source == "database"
        assert payload.numbers["police"].service == "100"

    def test_serializes_to_dict(self):
        payload = SosResponse(
            services=[_make_service_item()], count=1, radius_used=5000,
            source="database", numbers=EMERGENCY_NUMBERS.numbers,
        )
        data = payload.model_dump(mode="json")
        assert data["count"] == 1
        assert "services" in data
        assert "numbers" in data

    def test_includes_emergency_contacts(self):
        payload = SosResponse(
            services=[_make_service_item()], count=1, radius_used=5000,
            source="database", numbers=EMERGENCY_NUMBERS.numbers,
        )
        services = {num.service for num in payload.numbers.values()}
        assert "112" in services
        assert "100" in services


# ── _find_nearby_uncached ─────────────────────────────────────────────────────


class TestFindNearbyUncached:
    @patch.object(EmergencyLocatorService, "_search_local_catalog", return_value=[])
    async def test_steps_through_radius(self, mock_local, service, overpass_service):
        db = _db_mock(scalar_return=1)

        result = await service._find_nearby_uncached(
            db=db, lat=13.08, lon=80.27, categories=["hospital"],
            radius_steps=[500, 1000, 5000], limit=20,
        )

        assert result.count == 0
        assert db.execute.await_count >= 2

    @patch.object(EmergencyLocatorService, "_search_local_catalog", return_value=[])
    async def test_returns_empty(self, mock_local, service, overpass_service):
        db = _db_mock(scalar_return=0)
        overpass_service.search_services.return_value = []

        result = await service._find_nearby_uncached(
            db=db, lat=13.08, lon=80.27, categories=["hospital"],
            radius_steps=[5000], limit=20,
        )

        assert result.count == 0
        assert result.services == []
        assert result.source == "database"

    @patch.object(EmergencyLocatorService, "_search_local_catalog", return_value=[])
    async def test_next_offset(self, mock_local, service, overpass_service):
        db = _db_mock(scalar_return=25)
        overpass_service.search_services.return_value = []

        result = await service._find_nearby_uncached(
            db=db, lat=13.08, lon=80.27, categories=["hospital"],
            radius_steps=[5000], limit=20, offset=0,
        )

        assert result.next_offset == 20

    @patch.object(EmergencyLocatorService, "_search_local_catalog", return_value=[])
    async def test_next_offset_none_on_last_page(self, mock_local, service, overpass_service):
        db = _db_mock(scalar_return=15)
        overpass_service.search_services.return_value = []

        result = await service._find_nearby_uncached(
            db=db, lat=13.08, lon=80.27, categories=["hospital"],
            radius_steps=[5000], limit=20, offset=20,
        )

        assert result.next_offset is None

    @patch.object(EmergencyLocatorService, "_search_local_catalog", return_value=[])
    async def test_with_overpass(self, mock_local, service, overpass_service):
        db = _db_mock(scalar_return=0)
        overpass_service.search_services.return_value = [
            _make_service_item(id="op-1", name="Overpass Facility", source="overpass"),
        ]

        result = await service._find_nearby_uncached(
            db=db, lat=13.08, lon=80.27, categories=["hospital"],
            radius_steps=[5000], limit=20,
        )

        assert result.count == 1
        assert result.source == "overpass"

    @patch.object(EmergencyLocatorService, "_search_local_catalog", return_value=[])
    async def test_total_count(self, mock_local, service, overpass_service):
        db = _db_mock(scalar_return=42)
        overpass_service.search_services.return_value = []

        result = await service._find_nearby_uncached(
            db=db, lat=13.08, lon=80.27, categories=["hospital"],
            radius_steps=[5000], limit=20,
        )

        assert result.total_count == 42


# ── _query_healthsites ────────────────────────────────────────────────────────


class TestQueryHealthsites:
    async def test_returns_empty_without_api_key(self, service):
        result = await service._query_healthsites(lat=13.08, lon=80.27)
        assert result == []

    async def test_returns_empty_on_http_error(self, service):
        object.__setattr__(service.settings, 'healthsites_api_key', 'test-key')
        with patch("httpx.AsyncClient") as mock_cls:
            mock_inst = MagicMock()
            mock_cls.return_value = mock_inst
            mock_inst.__aenter__ = AsyncMock(return_value=mock_inst)
            mock_resp = MagicMock()
            mock_resp.is_success = False
            mock_inst.get = AsyncMock(return_value=mock_resp)
            result = await service._query_healthsites(lat=13.08, lon=80.27)
        assert result == []

    async def test_returns_empty_on_exception(self, service):
        object.__setattr__(service.settings, 'healthsites_api_key', 'test-key')
        with patch("httpx.AsyncClient") as mock_cls:
            mock_inst = MagicMock()
            mock_cls.return_value = mock_inst
            mock_inst.__aenter__ = AsyncMock(return_value=mock_inst)
            mock_inst.get = AsyncMock(side_effect=httpx.HTTPError("Request failed"))
            result = await service._query_healthsites(lat=13.08, lon=80.27)
        assert result == []

    async def test_parses_response(self, service):
        object.__setattr__(service.settings, 'healthsites_api_key', 'test-key')
        with patch("httpx.AsyncClient") as mock_cls:
            mock_inst = MagicMock()
            mock_cls.return_value = mock_inst
            mock_inst.__aenter__ = AsyncMock(return_value=mock_inst)
            mock_resp = MagicMock()
            mock_resp.is_success = True
            mock_resp.json.return_value = [
                {
                    "id": "hs-1",
                    "attributes": {
                        "name": "City Hospital", "amenity": "hospital",
                        "healthcare": "general", "phone": "12345", "address": "Main St",
                    },
                    "geometry": {"coordinates": [80.27, 13.08]},
                },
            ]
            mock_inst.get = AsyncMock(return_value=mock_resp)
            result = await service._query_healthsites(lat=13.08, lon=80.27)
        assert len(result) == 1
        assert result[0].name == "City Hospital"
        assert result[0].source == "healthsites.io"

    async def test_empty_response(self, service):
        object.__setattr__(service.settings, 'healthsites_api_key', 'test-key')
        with patch("httpx.AsyncClient") as mock_cls:
            mock_inst = MagicMock()
            mock_cls.return_value = mock_inst
            mock_inst.__aenter__ = AsyncMock(return_value=mock_inst)
            mock_resp = MagicMock()
            mock_resp.is_success = True
            mock_resp.json.return_value = []
            mock_inst.get = AsyncMock(return_value=mock_resp)
            result = await service._query_healthsites(lat=13.08, lon=80.27)
        assert result == []


# ── SOS dispatch concept tests ────────────────────────────────────────────────


class TestSosDispatch:
    @patch.object(EmergencyLocatorService, "_search_local_catalog", return_value=[])
    async def test_flow_with_services(self, mock_local, service, cache, overpass_service):
        cache.get_json.return_value = None
        db = _db_mock(scalar_return=0)
        overpass_service.search_services.return_value = [
            _make_service_item(id="h-1", name="Dispatch Hospital", category="hospital", source="overpass"),
        ]

        payload = await service.build_sos_payload(db=db, lat=13.08, lon=80.27)

        assert isinstance(payload, SosResponse)
        assert payload.count == 1
        assert payload.services[0].name == "Dispatch Hospital"

    @patch.object(EmergencyLocatorService, "_search_local_catalog", return_value=[])
    async def test_anonymous(self, mock_local, service, cache, overpass_service):
        cache.get_json.return_value = None
        db = _db_mock(scalar_return=0)
        overpass_service.search_services.return_value = []

        payload = await service.build_sos_payload(db=db, lat=13.08, lon=80.27)
        assert isinstance(payload, SosResponse)
        assert payload.numbers is not None

    @patch.object(EmergencyLocatorService, "_search_local_catalog", return_value=[])
    async def test_home_guard_fallback_numbers(self, mock_local, service, cache, overpass_service):
        cache.get_json.return_value = None
        db = _db_mock(scalar_return=0)
        overpass_service.search_services.return_value = []

        payload = await service.build_sos_payload(db=db, lat=13.08, lon=80.27)

        services = {num.service for num in payload.numbers.values()}
        assert "100" in services
        assert "102" in services
        assert "101" in services

    @patch.object(EmergencyLocatorService, "_search_local_catalog", return_value=[])
    async def test_external_error_propagates(self, mock_local, service, cache):
        cache.get_json.return_value = None
        cache.get_json_stale.return_value = None
        db = _db_mock(scalar_return=0)
        db.execute.side_effect = ExternalServiceError("Upstream timeout")

        with pytest.raises(ExternalServiceError, match="Upstream timeout"):
            await service.build_sos_payload(db=db, lat=13.08, lon=80.27)


# ── SUPPORTED_CATEGORIES ──────────────────────────────────────────────────────


class TestSupportedCategories:
    def test_all_strings(self):
        assert all(isinstance(c, str) for c in SUPPORTED_CATEGORIES)

    def test_all_lowercase(self):
        assert all(c == c.lower() for c in SUPPORTED_CATEGORIES)

    def test_known_categories(self):
        for cat in ("hospital", "police", "ambulance", "fire", "towing", "pharmacy", "puncture", "showroom"):
            assert cat in SUPPORTED_CATEGORIES

    def test_no_duplicates(self):
        assert len(SUPPORTED_CATEGORIES) == len(set(SUPPORTED_CATEGORIES))

    def test_count(self):
        assert len(SUPPORTED_CATEGORIES) == 8


# ── DEFAULT_EMERGENCY_NUMBERS_DATA ────────────────────────────────────────────


class TestDefaultEmergencyNumbersData:
    def test_all_have_service(self):
        for k, v in DEFAULT_EMERGENCY_NUMBERS_DATA.items():
            assert v.get("service"), f"{k} missing service"

    def test_all_have_coverage(self):
        for k, v in DEFAULT_EMERGENCY_NUMBERS_DATA.items():
            assert "coverage" in v, f"{k} missing coverage"

    def test_all_have_notes(self):
        for k, v in DEFAULT_EMERGENCY_NUMBERS_DATA.items():
            assert "notes" in v, f"{k} missing notes"

    def test_consistent_keys(self):
        keys = {frozenset(v.keys()) for v in DEFAULT_EMERGENCY_NUMBERS_DATA.values()}
        assert len(keys) == 1

    def test_has_13_entries(self):
        assert len(DEFAULT_EMERGENCY_NUMBERS_DATA) == 13


# ── _find_nearby edge cases ──────────────────────────────────────────────────


class TestFindNearbyEdgeCases:
    @patch.object(EmergencyLocatorService, "_search_local_catalog")
    async def test_database_and_local_merged(self, mock_local, service, cache, overpass_service):
        cache.get_json.return_value = None
        db_items = [_make_service_item(id="1", name="DB Hospital", source="database")]
        db = _db_mock_with_rows(db_items, total=1)
        overpass_service.search_services.return_value = []
        mock_local.return_value = [
            _make_service_item(id="2", name="Local Clinic", source="local_csv"),
        ]

        result = await service.find_nearby(db=db, lat=13.08, lon=80.27, categories=None)

        assert result.count == 2
        assert result.source == "database+local"

    @patch.object(EmergencyLocatorService, "_search_local_catalog")
    async def test_local_only_when_no_db_results(self, mock_local, service, cache, overpass_service):
        cache.get_json.return_value = None
        db = _db_mock(scalar_return=0)
        overpass_service.search_services.return_value = []
        mock_local.return_value = [
            _make_service_item(id="1", name="Local Only", source="local_csv"),
        ]

        result = await service.find_nearby(db=db, lat=13.08, lon=80.27, categories=None)

        assert result.count == 1
        assert result.source == "local"

    async def test_healthsites_flat_none_skipped(self, service):
        object.__setattr__(service.settings, 'healthsites_api_key', 'test-key')
        with patch("httpx.AsyncClient") as mock_cls:
            mock_inst = MagicMock()
            mock_cls.return_value = mock_inst
            mock_inst.__aenter__ = AsyncMock(return_value=mock_inst)
            mock_resp = MagicMock()
            mock_resp.is_success = True
            mock_resp.json.return_value = [
                {
                    "id": "hs-1",
                    "attributes": {"name": "Null Coord", "amenity": "hospital"},
                    "geometry": {"coordinates": [None, None]},
                },
                {
                    "id": "hs-2",
                    "attributes": {"name": "Good Hosp", "amenity": "hospital"},
                    "geometry": {"coordinates": [80.27, 13.08]},
                },
            ]
            mock_inst.get = AsyncMock(return_value=mock_resp)
            result = await service._query_healthsites(lat=13.08, lon=80.27)
        assert len(result) == 1
        assert result[0].id == "healthsites-hs-2"


# ── _find_nearby_uncached edge cases ──────────────────────────────────────────


class TestFindNearbyUncachedEdgeCases:
    @patch.object(EmergencyLocatorService, "_search_local_catalog", return_value=[])
    async def test_break_on_sufficient_results(self, mock_local, service, overpass_service):
        items = [_make_service_item(id=str(i), name=f"H{i}", source="database") for i in range(5)]
        db = _db_mock_with_rows(items, total=5)
        overpass_service.search_services.return_value = []

        result = await service._find_nearby_uncached(
            db=db, lat=13.08, lon=80.27, categories=["hospital"],
            radius_steps=[500, 1000, 5000], limit=20,
        )

        assert result.count == 5

    @patch.object(EmergencyLocatorService, "_search_local_catalog")
    async def test_database_local_overpass_all_sources(self, mock_local, service, overpass_service):
        db_items = [_make_service_item(id="1", name="DB", source="database")]
        db = _db_mock_with_rows(db_items, total=1)
        overpass_service.search_services.return_value = [
            _make_service_item(id="2", name="Overpass", source="overpass"),
        ]
        mock_local.return_value = [
            _make_service_item(id="3", name="Local", source="local_csv"),
        ]

        result = await service._find_nearby_uncached(
            db=db, lat=13.08, lon=80.27, categories=["hospital"],
            radius_steps=[1000, 5000], limit=20,
        )

        assert result.count == 3
        assert result.source == "database+local+overpass"

    @patch.object(EmergencyLocatorService, "_search_local_catalog", return_value=[])
    async def test_source_database_when_best_exists(self, mock_local, service, overpass_service):
        db_items = [_make_service_item(id="1", name="DB Hospital", source="database")]
        db = _db_mock_with_rows(db_items, total=1)
        overpass_service.search_services.return_value = []

        result = await service._find_nearby_uncached(
            db=db, lat=13.08, lon=80.27, categories=["hospital"],
            radius_steps=[5000], limit=20,
        )

        assert result.source == "database"

    @patch.object(EmergencyLocatorService, "_search_local_catalog", return_value=[])
    async def test_overpass_with_local_fallback_source(self, mock_local, service, overpass_service):
        db = _db_mock(scalar_return=0)
        overpass_service.search_services.return_value = []
        mock_local.return_value = [
            _make_service_item(id="1", name="Local Only", source="local_csv"),
        ]

        result = await service._find_nearby_uncached(
            db=db, lat=13.08, lon=80.27, categories=["hospital"],
            radius_steps=[5000], limit=20,
        )

        assert result.source == "local"
