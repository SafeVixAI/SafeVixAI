# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from models.city_center import CityCenter
from models.values import Coordinates, Distance, Severity
from services.city_center_repo import get_all_city_centers, get_city_center, get_offline_centers
from services.osm_contributor import OSM_TAG_MAP, OSMContributor, get_osm_contributor

# ── models/values.py tests ──────────────────────────────────────────────────

class TestCoordinates:
    def test_valid_coordinates(self):
        c = Coordinates(lat=13.0827, lon=80.2707)
        assert c.lat == 13.0827
        assert c.lon == 80.2707

    def test_invalid_lat_too_high(self):
        with pytest.raises(ValueError, match="lat must be in"):
            Coordinates(lat=91, lon=0)

    def test_invalid_lat_too_low(self):
        with pytest.raises(ValueError, match="lat must be in"):
            Coordinates(lat=-91, lon=0)

    def test_invalid_lon_too_high(self):
        with pytest.raises(ValueError, match="lon must be in"):
            Coordinates(lat=0, lon=181)

    def test_invalid_lon_too_low(self):
        with pytest.raises(ValueError, match="lon must be in"):
            Coordinates(lat=0, lon=-181)

    def test_boundary_values(self):
        c1 = Coordinates(lat=90, lon=180)
        assert c1.lat == 90
        c2 = Coordinates(lat=-90, lon=-180)
        assert c2.lat == -90

    def test_distance_to_self_is_zero(self):
        c = Coordinates(lat=13.0827, lon=80.2707)
        d = c.distance_to(c)
        assert d.meters == 0.0

    def test_distance_to_known(self):
        chennai = Coordinates(lat=13.0827, lon=80.2707)
        coimbatore = Coordinates(lat=11.0168, lon=76.9558)
        d = chennai.distance_to(coimbatore)
        assert 350_000 < d.meters < 550_000

    def test_as_tuple(self):
        c = Coordinates(lat=12.0, lon=77.0)
        assert c.as_tuple() == (12.0, 77.0)

    def test_frozen_dataclass(self):
        c = Coordinates(lat=1, lon=2)
        with pytest.raises(Exception):
            c.lat = 3


class TestSeverity:
    def test_valid_levels(self):
        for level in range(1, 6):
            s = Severity(level=level)
            assert s.level == level

    def test_invalid_too_low(self):
        with pytest.raises(ValueError, match="Severity must be 1-5"):
            Severity(level=0)

    def test_invalid_too_high(self):
        with pytest.raises(ValueError, match="Severity must be 1-5"):
            Severity(level=6)

    def test_labels(self):
        assert Severity(level=1).label == "low"
        assert Severity(level=2).label == "moderate"
        assert Severity(level=3).label == "high"
        assert Severity(level=4).label == "critical"
        assert Severity(level=5).label == "emergency"

    def test_unknown_label_via_bypass(self):
        s = object.__new__(Severity)
        object.__setattr__(s, "level", 99)
        assert s.label == "unknown"

    def test_is_critical(self):
        assert Severity(level=4).is_critical is True
        assert Severity(level=5).is_critical is True
        assert Severity(level=3).is_critical is False
        assert Severity(level=1).is_critical is False

    def test_from_int(self):
        s = Severity.from_int(3)
        assert s.level == 3


class TestDistance:
    def test_valid_distance(self):
        d = Distance(meters=100)
        assert d.meters == 100

    def test_zero_distance(self):
        d = Distance(meters=0)
        assert d.meters == 0

    def test_negative_distance_raises(self):
        with pytest.raises(ValueError, match="Distance must be non-negative"):
            Distance(meters=-1)

    def test_kilometers(self):
        d = Distance(meters=1500)
        assert d.kilometers == 1.5

    def test_comparison_lt(self):
        assert Distance(100) < Distance(200)
        assert not (Distance(200) < Distance(100))

    def test_comparison_le(self):
        assert Distance(100) <= Distance(100)
        assert Distance(100) <= Distance(200)

    def test_comparison_gt(self):
        assert Distance(200) > Distance(100)
        assert not (Distance(100) > Distance(200))

    def test_comparison_ge(self):
        assert Distance(100) >= Distance(100)
        assert Distance(200) >= Distance(100)

    def test_addition(self):
        d = Distance(100) + Distance(200)
        assert d.meters == 300

    def test_subtraction(self):
        d = Distance(200) - Distance(100)
        assert d.meters == 100

    def test_subtraction_never_negative(self):
        d = Distance(50) - Distance(200)
        assert d.meters == 0.0

    def test_frozen(self):
        d = Distance(meters=100)
        with pytest.raises(Exception):
            d.meters = 200


# ── models/city_center.py tests ─────────────────────────────────────────────

class TestCityCenterModel:
    def test_create_city_center(self):
        cc = CityCenter(
            city_slug="chennai",
            display_name="Chennai",
            lat=13.0827,
            lon=80.2707,
            is_offline_bundle=True,
            state="Tamil Nadu",
        )
        assert cc.city_slug == "chennai"
        assert cc.lat == 13.0827
        assert cc.is_offline_bundle is True

    def test_city_center_minimal(self):
        cc = CityCenter(city_slug="xyz", display_name="XYZ", lat=0, lon=0, is_offline_bundle=False)
        assert cc.is_offline_bundle is False
        assert cc.state is None
        assert cc.city_slug == "xyz"


def _async_db_result(rows=None):
    """Return an async callable that mimics db.execute returning rows."""
    rows = rows or []
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = rows
    return mock_result


# ── services/city_center_repo.py tests ──────────────────────────────────────

class TestCityCenterRepo:
    async def test_get_all_centers_no_db(self):
        result = await get_all_city_centers(db=None)
        assert "chennai" in result
        assert result["chennai"] == (13.0827, 80.2707)
        assert len(result) > 40

    async def test_get_all_centers_with_db_success(self):
        mock_db = MagicMock(spec=AsyncSession)
        mock_db.execute = AsyncMock()
        mock_db.execute.return_value = _async_db_result([
            CityCenter(city_slug="test_city", display_name="Test", lat=10.0, lon=20.0)
        ])

        result = await get_all_city_centers(db=mock_db)
        assert result["test_city"] == (10.0, 20.0)
        assert "chennai" not in result

    async def test_get_all_centers_db_empty_uses_fallback(self):
        mock_db = MagicMock(spec=AsyncSession)
        mock_db.execute = AsyncMock()
        mock_db.execute.return_value = _async_db_result([])

        result = await get_all_city_centers(db=mock_db)
        assert "chennai" in result

    async def test_get_all_centers_db_exception_uses_fallback(self):
        mock_db = MagicMock(spec=AsyncSession)
        mock_db.execute = AsyncMock(side_effect=Exception("DB error"))

        result = await get_all_city_centers(db=mock_db)
        assert "chennai" in result

    async def test_get_offline_centers_no_db(self):
        result = await get_offline_centers(db=None)
        assert "chennai" in result
        assert "agartala" not in result

    async def test_get_offline_centers_with_db(self):
        mock_db = MagicMock(spec=AsyncSession)
        mock_db.execute = AsyncMock()
        mock_db.execute.return_value = _async_db_result([
            CityCenter(city_slug="offline_city", display_name="Off", lat=1, lon=2, is_offline_bundle=True)
        ])

        result = await get_offline_centers(db=mock_db)
        assert result["offline_city"] == (1.0, 2.0)

    async def test_get_city_center_no_db(self):
        result = await get_city_center("chennai", db=None)
        assert result == (13.0827, 80.2707)

    async def test_get_city_center_not_found(self):
        result = await get_city_center("nonexistent_city_xyz", db=None)
        assert result is None

    async def test_get_city_center_with_db(self):
        mock_db = MagicMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = MagicMock(lat=99.0, lon=88.0)
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await get_city_center("test", db=mock_db)
        assert result == (99.0, 88.0)

    async def test_get_city_center_db_exception_uses_fallback(self):
        mock_db = MagicMock(spec=AsyncSession)
        mock_db.execute = AsyncMock(side_effect=Exception("DB error"))

        result = await get_city_center("chennai", db=mock_db)
        assert result == (13.0827, 80.2707)

    async def test_get_city_center_db_empty_uses_fallback(self):
        mock_db = MagicMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await get_city_center("chennai", db=mock_db)
        assert result == (13.0827, 80.2707)


# ── services/osm_contributor.py tests ───────────────────────────────────────

class TestOSMContributor:
    @pytest.mark.asyncio
    async def test_init_with_token(self):
        contributor = OSMContributor(access_token="test-token")
        assert contributor.is_configured is True
        assert contributor._access_token == "test-token"
        await contributor.close()

    @pytest.mark.asyncio
    async def test_init_without_token(self):
        contributor = OSMContributor(access_token="")
        assert contributor.is_configured is False
        await contributor.close()

    @pytest.mark.asyncio
    async def test_contribute_not_configured(self):
        c = OSMContributor(access_token="")
        result = await c.contribute_report({"lat": 1, "lon": 2, "issue_type": "pothole"})
        assert result["status"] == "skipped"
        await c.close()

    @pytest.mark.asyncio
    async def test_contribute_missing_coords(self):
        c = OSMContributor(access_token="token")
        result = await c.contribute_report({"issue_type": "pothole"})
        assert result["status"] == "error"
        assert "Missing coordinates" in result["reason"]
        await c.close()

    @pytest.mark.asyncio
    async def test_contribute_success(self):
        c = OSMContributor(access_token="token")
        with patch.object(c, "_open_changeset", AsyncMock(return_value="123")):
            with patch.object(c, "_create_node", AsyncMock(return_value="456")):
                with patch.object(c, "_close_changeset", AsyncMock(return_value=True)):
                    result = await c.contribute_report({
                        "lat": 13.0, "lon": 80.0, "issue_type": "pothole",
                        "description": "Deep pothole", "id": "ABC-123",
                        "road_name": "Anna Salai",
                    })
                    assert result["status"] == "success"
                    assert result["changeset_id"] == "123"
                    assert result["node_id"] == "456"
        await c.close()

    @pytest.mark.asyncio
    async def test_contribute_changeset_fails(self):
        c = OSMContributor(access_token="token")
        with patch.object(c, "_open_changeset", AsyncMock(return_value=None)):
            result = await c.contribute_report({
                "lat": 13.0, "lon": 80.0, "issue_type": "pothole"
            })
            assert result["status"] == "error"
        await c.close()

    @pytest.mark.asyncio
    async def test_contribute_node_fails_closes_changeset(self):
        c = OSMContributor(access_token="token")
        with patch.object(c, "_open_changeset", AsyncMock(return_value="123")):
            with patch.object(c, "_create_node", AsyncMock(return_value=None)):
                with patch.object(c, "_close_changeset", AsyncMock()) as mock_close:
                    result = await c.contribute_report({
                        "lat": 13.0, "lon": 80.0, "issue_type": "pothole"
                    })
                    assert result["status"] == "error"
                    mock_close.assert_called_once_with("123")
        await c.close()

    @pytest.mark.asyncio
    async def test_contribute_http_error(self):
        c = OSMContributor(access_token="token")
        with patch.object(c, "_open_changeset", AsyncMock(side_effect=httpx.HTTPError("HTTP 503"))):
            result = await c.contribute_report({
                "lat": 13.0, "lon": 80.0, "issue_type": "pothole"
            })
            assert result["status"] == "error"
        await c.close()

    @pytest.mark.asyncio
    async def test_open_changeset_success(self):
        c = OSMContributor(access_token="token")
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "98765"
        c._client.put = AsyncMock(return_value=mock_response)
        result = await c._open_changeset("pothole")
        assert result == "98765"
        await c.close()

    @pytest.mark.asyncio
    async def test_open_changeset_failure(self):
        c = OSMContributor(access_token="token")
        mock_response = MagicMock()
        mock_response.status_code = 409
        c._client.put = AsyncMock(return_value=mock_response)
        result = await c._open_changeset("pothole")
        assert result is None
        await c.close()

    @pytest.mark.asyncio
    async def test_open_changeset_http_error(self):
        c = OSMContributor(access_token="token")
        c._client.put = AsyncMock(side_effect=httpx.HTTPError("Timeout"))
        result = await c._open_changeset("pothole")
        assert result is None
        await c.close()

    @pytest.mark.asyncio
    async def test_create_node_success(self):
        c = OSMContributor(access_token="token")
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "555"
        c._client.put = AsyncMock(return_value=mock_response)
        result = await c._create_node("123", 13.0, 80.0, {"hazard": "yes"})
        assert result == "555"
        await c.close()

    @pytest.mark.asyncio
    async def test_create_node_failure(self):
        c = OSMContributor(access_token="token")
        mock_response = MagicMock()
        mock_response.status_code = 400
        c._client.put = AsyncMock(return_value=mock_response)
        result = await c._create_node("123", 13.0, 80.0, {"hazard": "yes"})
        assert result is None
        await c.close()

    @pytest.mark.asyncio
    async def test_close_changeset_success(self):
        c = OSMContributor(access_token="token")
        mock_response = MagicMock()
        mock_response.status_code = 200
        c._client.put = AsyncMock(return_value=mock_response)
        result = await c._close_changeset("123")
        assert result is True
        await c.close()

    @pytest.mark.asyncio
    async def test_close_changeset_failure(self):
        c = OSMContributor(access_token="token")
        c._client.put = AsyncMock(side_effect=httpx.HTTPError("Error"))
        result = await c._close_changeset("123")
        assert result is False
        await c.close()

    @pytest.mark.asyncio
    async def test_osm_tag_map_all_types(self):
        c = OSMContributor(access_token="token")
        assert "pothole" in OSM_TAG_MAP
        assert "highway" in OSM_TAG_MAP["pothole"]
        assert OSM_TAG_MAP["pothole"]["hazard"] == "yes"
        for issue_type in ["damaged_road", "flooding", "waterlogging", "broken_barrier",
                           "missing_sign", "accident", "landslide", "debris"]:
            assert issue_type in OSM_TAG_MAP, f"Missing OSM tag for {issue_type}"
        await c.close()

    @pytest.mark.asyncio
    async def test_unknown_issue_type_uses_default(self):
        c = OSMContributor(access_token="token")
        with patch.object(c, "_open_changeset", AsyncMock(return_value="1")):
            with patch.object(c, "_create_node", AsyncMock(return_value="2")):
                with patch.object(c, "_close_changeset", AsyncMock()):
                    result = await c.contribute_report({
                        "lat": 1, "lon": 2, "issue_type": "unknown_type_xyz"
                    })
                    assert result["status"] == "success"
        await c.close()

    @pytest.mark.asyncio
    async def test_get_osm_contributor_singleton(self):
        c1 = get_osm_contributor()
        c2 = get_osm_contributor()
        assert c1 is c2
        await c1.close()
