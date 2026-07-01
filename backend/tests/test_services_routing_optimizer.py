# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team
"""Service layer coverage: routing_service and officer_route_optimizer."""

from __future__ import annotations

import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from models.schemas import RoutePoint
from services.exceptions import ExternalServiceError, ServiceValidationError
from services.officer_route_optimizer import (
    OfficerRouteOptimizer,
    OfficerShift,
    _haversine_km,
    _nearest_neighbor_tsp,
)
from services.routing_service import RoutingService

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_settings():
    s = MagicMock()
    s.openrouteservice_api_key = None  # OSRM path by default
    s.openrouteservice_base_url = "https://api.openrouteservice.org"
    s.request_timeout_seconds = 30.0
    s.http_user_agent = "SafeVixAI-Test/1.0"
    s.route_cache_ttl_seconds = 300
    return s


@pytest.fixture
def mock_cache():
    c = MagicMock()
    c.get_json = AsyncMock(return_value=None)
    c.set_json = AsyncMock()
    return c


@pytest.fixture
async def service(mock_settings, mock_cache):
    """RoutingService with a live httpx client; properly closed after each test."""
    svc = RoutingService(settings=mock_settings, cache=mock_cache)
    yield svc
    await svc.aclose()


# ---------------------------------------------------------------------------
# Small data helpers
# ---------------------------------------------------------------------------


def _fake_resp(
    status_code: int = 200,
    json_data=None,
    json_raises: bool = False,
) -> MagicMock:
    """Minimal httpx.Response-like MagicMock."""
    resp = MagicMock()
    resp.status_code = status_code
    if json_raises:
        resp.json.side_effect = ValueError("not JSON")
    else:
        resp.json.return_value = {} if json_data is None else json_data
    return resp


def _osrm_payload(distance: float = 5000.0, duration: float = 600.0) -> dict:
    """Minimal OSRM /route/v1/driving JSON with two-point GeoJSON geometry."""
    return {
        "routes": [
            {
                "geometry": {"coordinates": [[80.0, 13.0], [80.1, 13.1]]},
                "legs": [],
                "distance": distance,
                "duration": duration,
            }
        ]
    }


def _ors_payload(distance: float = 5000.0, duration: float = 600.0) -> dict:
    """Minimal ORS /v2/directions/json response with two-point GeoJSON geometry."""
    return {
        "routes": [
            {
                "geometry": {"coordinates": [[80.0, 13.0], [80.1, 13.1]]},
                "summary": {"distance": distance, "duration": duration},
                "segments": [],
            }
        ]
    }


def _db_returning(issues: list) -> AsyncMock:
    """AsyncSession mock whose execute() returns *issues* via scalars().all()."""
    db = AsyncMock()
    result = MagicMock()
    scalars = MagicMock()
    scalars.all.return_value = issues
    result.scalars.return_value = scalars
    db.execute.return_value = result
    return db


def _issue(
    lat: object = 13.1,
    lon: object = 80.1,
    severity: int = 3,
    ref: str = "RS-001",
    issue_type: str = "pothole",
    ward_id: str | None = "W1",
    address: str | None = None,
) -> MagicMock:
    m = MagicMock()
    m.latitude = lat
    m.longitude = lon
    m.severity = severity
    m.complaint_ref = ref
    m.issue_type = issue_type
    m.ward_id = ward_id
    m.address = address
    # Prevent unexpected func.ST_Y() calls when lat is falsy/None
    m.location = MagicMock() if lat else None
    return m


# Minimal valid RoutePreviewResponse dict for cache-hit tests.
# Every required field must be present for model_validate() to succeed.
_CACHED_RESPONSE = {
    "provider": "osrm",
    "profile": "driving-car",
    "distance_meters": 5000.0,
    "duration_seconds": 600.0,
    "path": [{"lat": 13.0, "lon": 80.0}, {"lat": 13.1, "lon": 80.1}],
    "bounds": {"south": 13.0, "west": 80.0, "north": 13.1, "east": 80.1},
    "origin": {"lat": 13.0, "lon": 80.0, "label": "Current location"},
    "destination": {"lat": 13.1, "lon": 80.1, "label": "Destination"},
    "steps": [],
    "routes": [],
    "selected_route_id": "route-1",
    "reroute_threshold_meters": 75.0,
    "warnings": [],
}

_ALERT_PATH = "services.routing_service.get_alert_service"


# ===========================================================================
# 1.  RoutingService._same_point  (4 tests)
# ===========================================================================


def test_same_point_identical():
    assert RoutingService._same_point(13.0, 80.0, 13.0, 80.0) is True


def test_same_point_within_threshold():
    # Both axes differ by 5e-6, inside the 1e-5 boundary
    assert RoutingService._same_point(13.0, 80.0, 13.000005, 80.000005) is True


def test_same_point_beyond_threshold():
    # 2e-5 on both axes exceeds the threshold
    assert RoutingService._same_point(13.0, 80.0, 13.00002, 80.00002) is False


def test_same_point_only_lat_differs():
    assert RoutingService._same_point(13.0, 80.0, 13.00002, 80.0) is False


# ===========================================================================
# 2.  RoutingService._message_from_response  (7 tests)
# ===========================================================================


def test_message_error_key():
    resp = _fake_resp(200, {"error": "Route not found"})
    assert RoutingService._message_from_response(resp) == "Route not found"


def test_message_message_key():
    resp = _fake_resp(200, {"message": "Service unavailable"})
    assert RoutingService._message_from_response(resp) == "Service unavailable"


def test_message_nested_error_dict():
    # ORS-style: {"error": {"code": …, "message": "…"}}
    resp = _fake_resp(400, {"error": {"code": 2010, "message": "Invalid coordinates"}})
    assert RoutingService._message_from_response(resp) == "Invalid coordinates"


def test_message_non_json_body():
    resp = _fake_resp(500, json_raises=True)
    assert (
        RoutingService._message_from_response(resp)
        == "Routing provider could not generate a route right now."
    )


def test_message_429_rate_limit():
    resp = _fake_resp(429, {})
    assert "rate limit" in RoutingService._message_from_response(resp).lower()


def test_message_whitespace_only_error_falls_back():
    # strip() leaves empty string -> falls through to generic fallback
    resp = _fake_resp(200, {"error": "   "})
    assert (
        RoutingService._message_from_response(resp)
        == "Routing provider could not generate a route right now."
    )


def test_message_no_useful_keys():
    resp = _fake_resp(400, {"code": 42})
    assert (
        RoutingService._message_from_response(resp)
        == "Routing provider could not generate a route right now."
    )


# ===========================================================================
# 3.  RoutingService._decode_polyline  (3 tests)
# ===========================================================================


def test_decode_polyline_empty_string():
    assert RoutingService._decode_polyline("") == []


def test_decode_polyline_known_encoding():
    # "??_ibE_ibE" is the precision-5 Google Polyline encoding of
    # [(0.0, 0.0), (1.0, 1.0)], verified by hand:
    #   '?' -> ord(63)-63=0 <0x20 -> result_val=0, delta=0 -> lat=0, lng=0
    #   '_ibE' -> result_val=200_000, even -> delta=100_000 -> 1.0 on both axes
    result = RoutingService._decode_polyline("??_ibE_ibE", precision=5)
    assert len(result) == 2
    assert result[0] == (0.0, 0.0)
    assert result[1] == (1.0, 1.0)


def test_decode_polyline_returns_list_of_tuples():
    result = RoutingService._decode_polyline("??_ibE_ibE")
    for point in result:
        assert isinstance(point, tuple)
        assert len(point) == 2


# ===========================================================================
# 4.  RoutingService._build_bounds  (3 tests)
# ===========================================================================


def test_build_bounds_two_points():
    path = [RoutePoint(lat=13.0, lon=80.0), RoutePoint(lat=13.1, lon=80.1)]
    b = RoutingService._build_bounds(path)
    assert b.south == 13.0
    assert b.north == 13.1
    assert b.west == 80.0
    assert b.east == 80.1


def test_build_bounds_multiple_points_extremes():
    path = [
        RoutePoint(lat=13.0, lon=80.0),
        RoutePoint(lat=14.5, lon=79.0),
        RoutePoint(lat=12.0, lon=81.5),
    ]
    b = RoutingService._build_bounds(path)
    assert b.south == 12.0
    assert b.north == 14.5
    assert b.west == 79.0
    assert b.east == 81.5


def test_build_bounds_collinear_latitude():
    # Identical latitudes: south == north
    path = [RoutePoint(lat=13.0, lon=80.0), RoutePoint(lat=13.0, lon=81.0)]
    b = RoutingService._build_bounds(path)
    assert b.south == b.north == 13.0
    assert b.west == 80.0
    assert b.east == 81.0


# ===========================================================================
# 5.  RoutingService._normalize_osrm_route  (4 tests)
# ===========================================================================


def test_normalize_osrm_basic_success(service):
    route_data = {
        "geometry": {"coordinates": [[80.0, 13.0], [80.1, 13.1]]},
        "legs": [],
        "distance": 5000.0,
        "duration": 600.0,
    }
    result = service._normalize_osrm_route(route_data, index=1)
    assert result.route_id == "route-1"
    assert result.label == "Primary route"
    assert result.distance_meters == 5000.0
    assert result.duration_seconds == 600.0
    assert len(result.path) == 2
    # GeoJSON is [lon, lat]; first pair [80.0, 13.0] -> lat=13.0, lon=80.0
    assert result.path[0].lat == 13.0
    assert result.path[0].lon == 80.0


def test_normalize_osrm_alternative_label(service):
    route_data = {
        "geometry": {"coordinates": [[80.0, 13.0], [80.1, 13.1]]},
        "legs": [],
        "distance": 4000.0,
        "duration": 500.0,
    }
    assert service._normalize_osrm_route(route_data, index=2).label == "Alternative 1"
    assert service._normalize_osrm_route(route_data, index=3).label == "Alternative 2"


def test_normalize_osrm_fallback_to_maneuver_locations(service):
    # Empty GeoJSON coords -> fallback reads step maneuver.location values
    route_data = {
        "geometry": {"coordinates": []},
        "legs": [
            {
                "steps": [
                    {
                        "maneuver": {"type": "depart", "location": [80.0, 13.0]},
                        "name": "",
                        "distance": 0.0,
                        "duration": 0.0,
                    },
                    {
                        "maneuver": {"type": "arrive", "location": [80.1, 13.1]},
                        "name": "",
                        "distance": 500.0,
                        "duration": 60.0,
                    },
                ]
            }
        ],
        "distance": 500.0,
        "duration": 60.0,
    }
    result = service._normalize_osrm_route(route_data, index=1)
    assert len(result.path) == 2
    assert result.path[0].lat == 13.0
    assert result.path[1].lat == 13.1


def test_normalize_osrm_too_few_points_raises(service):
    route_data = {"geometry": {"coordinates": []}, "legs": [], "distance": 0.0, "duration": 0.0}
    with pytest.raises(ExternalServiceError, match="invalid path coordinates"):
        service._normalize_osrm_route(route_data, index=1)


# ===========================================================================
# 6.  RoutingService._normalize_ors_route  (4 tests)
# ===========================================================================


def test_normalize_ors_dict_geometry(service):
    route_data = {
        "geometry": {"coordinates": [[80.0, 13.0], [80.1, 13.1]]},
        "summary": {"distance": 5000.0, "duration": 600.0},
        "segments": [],
    }
    result = service._normalize_ors_route(route_data, index=1)
    assert result.route_id == "route-1"
    assert result.label == "Primary route"
    assert result.distance_meters == 5000.0
    assert len(result.path) == 2
    assert result.path[0].lat == 13.0


def test_normalize_ors_string_geometry(service):
    # "??_ibE_ibE" decodes to [(0.0, 0.0), (1.0, 1.0)];
    # both points are within RoutePoint lat/lon constraint bounds.
    route_data = {
        "geometry": "??_ibE_ibE",
        "summary": {"distance": 8000.0, "duration": 900.0},
        "segments": [],
    }
    result = service._normalize_ors_route(route_data, index=1)
    assert len(result.path) == 2
    assert result.path[0].lat == 0.0
    assert result.path[1].lat == 1.0


def test_normalize_ors_too_few_points_raises(service):
    route_data = {
        "geometry": {"coordinates": [[80.0, 13.0]]},  # Only 1 coord
        "summary": {"distance": 0.0, "duration": 0.0},
        "segments": [],
    }
    with pytest.raises(ExternalServiceError, match="ORS returned invalid route geometry"):
        service._normalize_ors_route(route_data, index=1)


def test_normalize_ors_segments_steps_parsed(service):
    route_data = {
        "geometry": {"coordinates": [[80.0, 13.0], [80.1, 13.1]]},
        "summary": {"distance": 5000.0, "duration": 600.0},
        "segments": [
            {
                "steps": [
                    {
                        "instruction": "Turn left onto MG Road",
                        "distance": 2000.0,
                        "duration": 120.0,
                        "name": "MG Road",
                    }
                ]
            }
        ],
    }
    result = service._normalize_ors_route(route_data, index=1)
    assert len(result.steps) == 1
    assert result.steps[0].instruction == "Turn left onto MG Road"
    assert result.steps[0].street_name == "MG Road"
    assert result.steps[0].distance_meters == 2000.0


# ===========================================================================
# 7.  RoutingService.preview_route  (11 async tests)
# ===========================================================================


@pytest.mark.asyncio
async def test_preview_same_point_raises(service):
    with pytest.raises(ServiceValidationError, match="too close"):
        await service.preview_route(
            origin_lat=13.0,
            origin_lon=80.0,
            destination_lat=13.0,
            destination_lon=80.0,
        )


@pytest.mark.asyncio
async def test_preview_cache_hit_returns_early(service, mock_cache):
    mock_cache.get_json.return_value = _CACHED_RESPONSE
    result = await service.preview_route(
        origin_lat=13.0,
        origin_lon=80.0,
        destination_lat=13.1,
        destination_lon=80.1,
    )
    assert result.provider == "osrm"
    assert result.distance_meters == 5000.0
    # On a cache hit no HTTP write-back should happen
    mock_cache.set_json.assert_not_awaited()


@pytest.mark.asyncio
async def test_preview_osrm_success(service, mock_cache):
    mock_resp = _fake_resp(200, _osrm_payload())
    with patch.object(service._client, "get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        result = await service.preview_route(
            origin_lat=13.0,
            origin_lon=80.0,
            destination_lat=13.1,
            destination_lon=80.1,
        )
    assert result.provider == "osrm"
    assert result.profile == "driving-car"
    assert result.selected_route_id == "route-1"
    assert any("OSRM" in w for w in result.warnings)


@pytest.mark.asyncio
async def test_preview_osrm_http_error_raises(service, mock_cache):
    with patch(_ALERT_PATH) as mock_alert:
        mock_alert.return_value = MagicMock()
        with patch.object(
            service._client,
            "get",
            new_callable=AsyncMock,
            side_effect=httpx.ConnectError("refused"),
        ):
            with pytest.raises(ExternalServiceError, match="OSRM"):
                await service.preview_route(
                    origin_lat=13.0,
                    origin_lon=80.0,
                    destination_lat=13.1,
                    destination_lon=80.1,
                )


@pytest.mark.asyncio
async def test_preview_osrm_status_400_raises(service, mock_cache):
    mock_resp = _fake_resp(400, {"error": "Bad request"})
    with patch.object(service._client, "get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        with pytest.raises(ExternalServiceError):
            await service.preview_route(
                origin_lat=13.0,
                origin_lon=80.0,
                destination_lat=13.1,
                destination_lon=80.1,
            )


@pytest.mark.asyncio
async def test_preview_osrm_empty_routes_raises(service, mock_cache):
    mock_resp = _fake_resp(200, {"routes": []})
    with patch.object(service._client, "get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        with pytest.raises(ExternalServiceError, match="no route"):
            await service.preview_route(
                origin_lat=13.0,
                origin_lon=80.0,
                destination_lat=13.1,
                destination_lon=80.1,
            )


@pytest.mark.asyncio
async def test_preview_ors_success(service, mock_cache, mock_settings):
    # Enable ORS by setting an API key; preview_route reads it at call time
    mock_settings.openrouteservice_api_key = "test-ors-key"
    mock_resp = _fake_resp(200, _ors_payload())
    with patch.object(service._client, "post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        result = await service.preview_route(
            origin_lat=13.0,
            origin_lon=80.0,
            destination_lat=13.1,
            destination_lon=80.1,
        )
    assert result.provider == "ors"
    mock_post.assert_awaited_once()


@pytest.mark.asyncio
async def test_preview_ors_http_error_raises(service, mock_cache, mock_settings):
    mock_settings.openrouteservice_api_key = "test-ors-key"
    with patch(_ALERT_PATH) as mock_alert:
        mock_alert.return_value = MagicMock()
        with patch.object(
            service._client,
            "post",
            new_callable=AsyncMock,
            side_effect=httpx.TimeoutException("timeout"),
        ):
            with pytest.raises(ExternalServiceError, match="ORS"):
                await service.preview_route(
                    origin_lat=13.0,
                    origin_lon=80.0,
                    destination_lat=13.1,
                    destination_lon=80.1,
                )


@pytest.mark.asyncio
async def test_preview_alternatives_clamped_to_zero(service, mock_cache):
    # alternatives=-5 -> max(0, min(-5, 2))=0 -> 'alternatives' absent from GET params
    mock_resp = _fake_resp(200, _osrm_payload())
    with patch.object(service._client, "get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        await service.preview_route(
            origin_lat=13.0,
            origin_lon=80.0,
            destination_lat=13.1,
            destination_lon=80.1,
            alternatives=-5,
        )
    params = mock_get.call_args.kwargs.get("params", {})
    assert "alternatives" not in params


@pytest.mark.asyncio
async def test_preview_alternatives_clamped_to_two(service, mock_cache):
    # alternatives=99 -> max(0, min(99, 2))=2
    mock_resp = _fake_resp(200, _osrm_payload())
    with patch.object(service._client, "get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        await service.preview_route(
            origin_lat=13.0,
            origin_lon=80.0,
            destination_lat=13.1,
            destination_lon=80.1,
            alternatives=99,
        )
    params = mock_get.call_args.kwargs.get("params", {})
    assert params.get("alternatives") == "2"


@pytest.mark.asyncio
async def test_preview_cache_set_on_success(service, mock_cache):
    mock_resp = _fake_resp(200, _osrm_payload())
    with patch.object(service._client, "get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        await service.preview_route(
            origin_lat=13.0,
            origin_lon=80.0,
            destination_lat=13.1,
            destination_lon=80.1,
        )
    mock_cache.set_json.assert_awaited_once()
    key = mock_cache.set_json.call_args.args[0]
    assert key.startswith("route:preview:")


# ===========================================================================
# 8.  _haversine_km  (4 tests)
# ===========================================================================


def test_haversine_same_point():
    assert abs(_haversine_km(13.0, 80.0, 13.0, 80.0)) < 1e-6


def test_haversine_approx_one_km():
    # 0.009 degrees north ~ 1 km along the latitude axis near the equator
    dist = _haversine_km(13.0, 80.0, 13.009, 80.0)
    assert 0.9 < dist < 1.1


def test_haversine_symmetry():
    d1 = _haversine_km(13.0, 80.0, 14.0, 81.0)
    d2 = _haversine_km(14.0, 81.0, 13.0, 80.0)
    assert abs(d1 - d2) < 1e-9


def test_haversine_positive():
    assert _haversine_km(0.0, 0.0, 1.0, 1.0) > 0


# ===========================================================================
# 9.  _nearest_neighbor_tsp  (5 tests)
# ===========================================================================


def test_tsp_empty():
    assert _nearest_neighbor_tsp([], 13.0, 80.0) == []


def test_tsp_single_point():
    p = {"lat": 13.1, "lon": 80.1, "severity": 3}
    result = _nearest_neighbor_tsp([p], 13.0, 80.0)
    assert len(result) == 1
    assert result[0] is p


def test_tsp_visits_all_points():
    points = [
        {"lat": 13.1, "lon": 80.1, "severity": 3},
        {"lat": 13.2, "lon": 80.2, "severity": 3},
        {"lat": 13.3, "lon": 80.3, "severity": 3},
    ]
    result = _nearest_neighbor_tsp(points, 13.0, 80.0)
    assert len(result) == 3
    # Greedy nearest-neighbor from (13.0, 80.0) picks the closest point first
    assert result[0] is points[0]


def test_tsp_nearest_first():
    p_close = {"lat": 13.0, "lon": 80.005, "severity": 3}
    p_far = {"lat": 13.0, "lon": 80.050, "severity": 3}
    result = _nearest_neighbor_tsp([p_far, p_close], 13.0, 80.0)
    assert result[0] is p_close
    assert result[1] is p_far


def test_tsp_severity_bonus_elevates_high_priority():
    # p_close  (~0.11 km, severity=3): adjusted_d = 0.11  (no bonus)
    # p_sev6   (~1.11 km, severity=6): bonus = 1.5 km
    #           -> adjusted_d = max(0.01, 1.11 - 1.5) = 0.01
    # -> p_sev6 beats p_close despite being physically farther
    p_close = {"lat": 13.0, "lon": 80.001, "severity": 3}
    p_sev6 = {"lat": 13.0, "lon": 80.010, "severity": 6}
    result = _nearest_neighbor_tsp([p_close, p_sev6], 13.0, 80.0)
    assert result[0] is p_sev6


# ===========================================================================
# 10. OfficerRouteOptimizer.optimize_route  (8 async tests)
# ===========================================================================


@pytest.mark.asyncio
async def test_optimize_no_issues_returns_warning():
    db = _db_returning([])
    result = await OfficerRouteOptimizer.optimize_route(
        db,
        officer_id="o1",
        officer_lat=13.0,
        officer_lon=80.0,
    )
    assert result.total_stops == 0
    assert result.total_distance_km == 0
    assert result.stops == []
    assert any("No open complaints" in w for w in result.warnings)


@pytest.mark.asyncio
async def test_optimize_none_latitude_issue_skipped():
    # latitude=None -> `if hasattr(...) and issue.latitude` is False -> continue
    bad = _issue(lat=None, lon=None)
    bad.location = None
    db = _db_returning([bad])
    result = await OfficerRouteOptimizer.optimize_route(
        db,
        officer_id="o1",
        officer_lat=13.0,
        officer_lon=80.0,
    )
    assert result.total_stops == 0


@pytest.mark.asyncio
async def test_optimize_valid_issue_included():
    i = _issue(lat=13.1, lon=80.1, severity=4, ref="RS-042", issue_type="pothole", ward_id="W9")
    db = _db_returning([i])
    result = await OfficerRouteOptimizer.optimize_route(
        db,
        officer_id="o2",
        officer_lat=13.0,
        officer_lon=80.0,
    )
    assert result.total_stops == 1
    stop = result.stops[0]
    assert stop.order == 1
    assert stop.complaint_ref == "RS-042"
    assert stop.issue_type == "pothole"
    assert stop.severity == 4
    assert stop.lat == 13.1
    assert stop.lon == 80.1
    assert stop.ward_id == "W9"


@pytest.mark.asyncio
async def test_optimize_bad_coords_skipped():
    # latitude="bad" is truthy but float("bad") raises ValueError -> issue skipped
    bad = _issue(lat="bad", lon="bad")
    db = _db_returning([bad])
    result = await OfficerRouteOptimizer.optimize_route(
        db,
        officer_id="o1",
        officer_lat=13.0,
        officer_lon=80.0,
    )
    assert result.total_stops == 0


@pytest.mark.asyncio
async def test_optimize_city_filter_no_error():
    # Passing city= should not cause errors; DB is mocked to return no issues
    db = _db_returning([])
    result = await OfficerRouteOptimizer.optimize_route(
        db,
        officer_id="o1",
        officer_lat=13.0,
        officer_lon=80.0,
        city="Chennai",
    )
    assert result.officer_id == "o1"
    assert result.total_stops == 0
    db.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_optimize_ward_filter_preserves_ward_id():
    i = _issue(lat=13.1, lon=80.1, ward_id="W7")
    db = _db_returning([i])
    result = await OfficerRouteOptimizer.optimize_route(
        db,
        officer_id="o3",
        officer_lat=13.0,
        officer_lon=80.0,
        ward_id="W7",
    )
    assert result.total_stops == 1
    assert result.stops[0].ward_id == "W7"


@pytest.mark.asyncio
async def test_optimize_shift_overflow_warning():
    from datetime import time as dtime

    # 1-hour shift; 4 stops x 20 min each = 80 min > 60 min -> overflow warning
    tiny_shift = OfficerShift(
        start_time=dtime(9, 0),
        end_time=dtime(10, 0),
        max_complaints_per_shift=12,
        avg_minutes_per_stop=20,
    )
    issues = [_issue(lat=13.0 + i * 0.001, lon=80.0, ref=f"RS-{i:03d}") for i in range(1, 5)]
    db = _db_returning(issues)
    result = await OfficerRouteOptimizer.optimize_route(
        db,
        officer_id="o4",
        officer_lat=13.0,
        officer_lon=80.0,
        shift=tiny_shift,
    )
    assert any("exceeds shift" in w for w in result.warnings)


@pytest.mark.asyncio
async def test_optimize_caps_at_max_per_shift():
    shift = OfficerShift(max_complaints_per_shift=2)
    # Mock DB returns 5 issues; points[:2] caps to 2 stops
    issues = [_issue(lat=13.0 + i * 0.01, lon=80.0, ref=f"RS-{i:03d}") for i in range(1, 6)]
    db = _db_returning(issues)
    result = await OfficerRouteOptimizer.optimize_route(
        db,
        officer_id="o5",
        officer_lat=13.0,
        officer_lon=80.0,
        shift=shift,
    )
    assert result.total_stops == 2
    assert len(result.stops) == 2
