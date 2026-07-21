# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Tests for RoutingService — 90%+ coverage."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from core.config import Settings
from core.redis_client import CacheHelper
from models.schemas import (
    RouteBounds,
    RouteOption,
    RoutePoint,
    RoutePreviewResponse,
)
from services.exceptions import ExternalServiceError, ServiceValidationError
from services.routing_service import RoutingService


# ---------------------------------------------------------------------------
# Test fixtures
# ---------------------------------------------------------------------------

_ORS_ROUTE = {
    "geometry": {"coordinates": [[12.0, 13.0], [12.05, 13.03], [12.1, 13.1]]},
    "summary": {"distance": 15000.0, "duration": 900.0},
    "segments": [
        {
            "steps": [
                {
                    "instruction": "Head east on Main St",
                    "distance": 5000.0,
                    "duration": 300.0,
                    "name": "Main St",
                },
                {
                    "instruction": "Turn right onto Oak Ave",
                    "distance": 10000.0,
                    "duration": 600.0,
                    "name": "Oak Ave",
                },
            ]
        }
    ],
}

_ORS_RESPONSE: dict = {"routes": [_ORS_ROUTE]}

_CACHED_RESPONSE: dict = {
    "provider": "ors",
    "profile": "driving-car",
    "distance_meters": 15000.0,
    "duration_seconds": 900.0,
    "path": [
        {"lat": 13.0, "lon": 12.0},
        {"lat": 13.03, "lon": 12.05},
        {"lat": 13.1, "lon": 12.1},
    ],
    "bounds": {"south": 13.0, "west": 12.0, "north": 13.1, "east": 12.1},
    "origin": {"lat": 13.0, "lon": 12.0, "label": "Current location"},
    "destination": {"lat": 13.1, "lon": 12.1, "label": "Destination"},
    "steps": [
        {
            "index": 1,
            "instruction": "Head east on Main St",
            "distance_meters": 5000.0,
            "duration_seconds": 300.0,
            "street_name": "Main St",
        },
        {
            "index": 2,
            "instruction": "Turn right onto Oak Ave",
            "distance_meters": 10000.0,
            "duration_seconds": 600.0,
            "street_name": "Oak Ave",
        },
    ],
    "routes": [
        {
            "route_id": "route-1",
            "label": "Primary route",
            "distance_meters": 15000.0,
            "duration_seconds": 900.0,
            "path": [
                {"lat": 13.0, "lon": 12.0},
                {"lat": 13.03, "lon": 12.05},
                {"lat": 13.1, "lon": 12.1},
            ],
            "bounds": {"south": 13.0, "west": 12.0, "north": 13.1, "east": 12.1},
            "steps": [
                {
                    "index": 1,
                    "instruction": "Head east on Main St",
                    "distance_meters": 5000.0,
                    "duration_seconds": 300.0,
                    "street_name": "Main St",
                },
                {
                    "index": 2,
                    "instruction": "Turn right onto Oak Ave",
                    "distance_meters": 10000.0,
                    "duration_seconds": 600.0,
                    "street_name": "Oak Ave",
                },
            ],
        }
    ],
    "selected_route_id": "route-1",
    "reroute_threshold_meters": 75.0,
    "warnings": [],
}


@pytest.fixture
def settings():
    s = Settings()
    s.openrouteservice_api_key = "test-ors-key"
    s.openrouteservice_base_url = "https://api.openrouteservice.org"
    s.http_user_agent = "SafeVixAI/1.0"
    s.request_timeout_seconds = 20.0
    s.route_cache_ttl_seconds = 900
    return s


@pytest.fixture
def osrm_settings():
    s = Settings()
    s.openrouteservice_api_key = None
    s.openrouteservice_base_url = "https://api.openrouteservice.org"
    s.http_user_agent = "SafeVixAI/1.0"
    s.request_timeout_seconds = 20.0
    s.route_cache_ttl_seconds = 900
    return s


@pytest.fixture
def cache():
    return AsyncMock(spec=CacheHelper)


@pytest.fixture(autouse=True)
def _no_alert():
    with patch("services.routing_service.get_alert_service") as m:
        m.return_value = MagicMock()
        yield


@pytest.fixture
def ors_svc(settings, cache):
    svc = RoutingService(settings, cache)
    svc._client = AsyncMock()
    return svc


@pytest.fixture
def osrm_svc(osrm_settings, cache):
    svc = RoutingService(osrm_settings, cache)
    svc._client = AsyncMock()
    return svc


def _mock_http_200(data: dict) -> MagicMock:
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = 200
    resp.json.return_value = data
    return resp


# ===================================================================
# 1 — Constructor
# ===================================================================

class TestConstructor:
    @pytest.mark.asyncio
    async def test_creates_http_client_with_correct_config(self, settings, cache):
        with patch("services.routing_service.httpx.AsyncClient") as mock_cls:
            fake = AsyncMock()
            mock_cls.return_value = fake
            svc = RoutingService(settings, cache)

            mock_cls.assert_called_once_with(
                timeout=20.0,
                headers={
                    "Accept": "application/json",
                    "User-Agent": "SafeVixAI/1.0",
                },
            )
            assert svc._client is fake
            assert svc.settings is settings
            assert svc.cache is cache

    @pytest.mark.asyncio
    async def test_aclose_cleans_up_client(self, settings, cache):
        svc = RoutingService(settings, cache)
        svc._client = AsyncMock()
        await svc.aclose()
        svc._client.aclose.assert_awaited_once()


# ===================================================================
# 3-5 — _same_point
# ===================================================================

class TestSamePoint:
    @pytest.mark.asyncio
    async def test_true_when_coordinates_identical(self, settings, cache):
        svc = RoutingService(settings, cache)
        assert svc._same_point(13.0, 80.0, 13.0, 80.0) is True

    @pytest.mark.asyncio
    async def test_false_when_coordinates_different(self, settings, cache):
        svc = RoutingService(settings, cache)
        assert svc._same_point(13.0, 80.0, 13.1, 80.1) is False

    @pytest.mark.asyncio
    async def test_true_within_threshold(self, settings, cache):
        svc = RoutingService(settings, cache)
        # 1e-5 = 0.00001; 0.000009 is less → same point
        assert svc._same_point(13.00001, 80.0, 13.000011, 80.0) is True
        assert svc._same_point(13.0, 80.000001, 13.0, 80.0) is True


# ===================================================================
# 6-11 — preview_route
# ===================================================================

class TestPreviewRoute:
    # 6 — origin/dest too close
    @pytest.mark.asyncio
    async def test_raises_validation_error_when_points_too_close(self, ors_svc, cache):
        with pytest.raises(ServiceValidationError, match="too close"):
            await ors_svc.preview_route(
                origin_lat=13.0, origin_lon=80.0,
                destination_lat=13.000001, destination_lon=80.0,
            )
        cache.get_json.assert_not_called()

    # 7 — cache hit
    @pytest.mark.asyncio
    async def test_returns_cached_response(self, ors_svc, cache):
        cache.get_json.return_value = _CACHED_RESPONSE

        result = await ors_svc.preview_route(
            origin_lat=13.0, origin_lon=12.0,
            destination_lat=13.1, destination_lon=12.1,
        )

        assert isinstance(result, RoutePreviewResponse)
        assert result.distance_meters == 15000.0
        assert result.duration_seconds == 900.0
        assert result.provider == "ors"
        assert result.selected_route_id == "route-1"
        ors_svc._client.post.assert_not_called()
        cache.set_json.assert_not_called()

    # 8 — ORS success with validation
    @pytest.mark.asyncio
    async def test_ors_success_returns_parsed_response(self, ors_svc, cache):
        ors_svc._client.post = AsyncMock(return_value=_mock_http_200(_ORS_RESPONSE))
        cache.get_json.return_value = None

        result = await ors_svc.preview_route(
            origin_lat=13.0, origin_lon=12.0,
            destination_lat=13.1, destination_lon=12.1,
        )

        assert isinstance(result, RoutePreviewResponse)
        assert result.provider == "ors"
        assert result.profile == "driving-car"
        assert result.distance_meters == 15000.0
        assert result.duration_seconds == 900.0
        assert len(result.path) == 3
        assert result.path[0].lat == 13.0
        assert result.path[0].lon == 12.0
        assert result.origin.lat == 13.0
        assert result.origin.lon == 12.0
        assert result.origin.label == "Current location"
        assert result.destination.lat == 13.1
        assert result.destination.lon == 12.1
        assert result.destination.label == "Destination"
        assert result.selected_route_id == "route-1"
        assert len(result.routes) == 1
        assert result.routes[0].route_id == "route-1"
        assert result.routes[0].label == "Primary route"
        assert len(result.steps) == 2
        assert result.steps[0].instruction == "Head east on Main St"
        assert result.steps[1].street_name == "Oak Ave"
        assert result.bounds.south == 13.0
        assert result.bounds.north == 13.1
        assert result.bounds.west == 12.0
        assert result.bounds.east == 12.1
        assert result.warnings == []

        ors_svc._client.post.assert_called_once_with(
            "https://api.openrouteservice.org/v2/directions/driving-car/json",
            json={
                "coordinates": [[12.0, 13.0], [12.1, 13.1]],
                "preference": "recommended",
                "instructions": True,
                "alternative_routes": {"target_count": 2, "weight_factor": 1.4},
            },
            headers={"Authorization": "test-ors-key"},
        )
        cache.set_json.assert_awaited_once()

    # 9 — ORS HTTP error 4xx
    @pytest.mark.asyncio
    async def test_ors_http_error_raises_external_error(self, ors_svc, cache):
        resp = MagicMock(spec=httpx.Response)
        resp.status_code = 403
        resp.json.return_value = {"error": "Forbidden"}
        ors_svc._client.post = AsyncMock(return_value=resp)
        cache.get_json.return_value = None

        with pytest.raises(ExternalServiceError, match="Forbidden"):
            await ors_svc.preview_route(
                origin_lat=13.0, origin_lon=12.0,
                destination_lat=13.1, destination_lon=12.1,
            )

    # 10 — ORS empty routes
    @pytest.mark.asyncio
    async def test_ors_empty_routes_raises_external_error(self, ors_svc, cache):
        ors_svc._client.post = AsyncMock(
            return_value=_mock_http_200({"routes": []})
        )
        cache.get_json.return_value = None

        with pytest.raises(ExternalServiceError, match="no route"):
            await ors_svc.preview_route(
                origin_lat=13.0, origin_lon=12.0,
                destination_lat=13.1, destination_lon=12.1,
            )

    # 10b — ORS missing routes key
    @pytest.mark.asyncio
    async def test_ors_missing_routes_key_raises_external_error(self, ors_svc, cache):
        ors_svc._client.post = AsyncMock(
            return_value=_mock_http_200({})
        )
        cache.get_json.return_value = None

        with pytest.raises(ExternalServiceError, match="no route"):
            await ors_svc.preview_route(
                origin_lat=13.0, origin_lon=12.0,
                destination_lat=13.1, destination_lon=12.1,
            )

    # 11 — ORS timeout / httpx.HTTPError
    @pytest.mark.asyncio
    async def test_ors_http_exception_raises_external_error(self, ors_svc, cache):
        ors_svc._client.post = AsyncMock(
            side_effect=httpx.TimeoutException("Connection timed out")
        )
        cache.get_json.return_value = None

        with pytest.raises(ExternalServiceError, match="Unable to reach ORS"):
            await ors_svc.preview_route(
                origin_lat=13.0, origin_lon=12.0,
                destination_lat=13.1, destination_lon=12.1,
            )

    # 12 — ORS body without alternatives
    @pytest.mark.asyncio
    async def test_ors_body_without_alternatives(self, ors_svc, cache):
        empty_route = {
            "geometry": {"coordinates": [[12.0, 13.0], [12.1, 13.1]]},
            "summary": {"distance": 1000.0, "duration": 60.0},
            "segments": [],
        }
        ors_svc._client.post = AsyncMock(
            return_value=_mock_http_200({"routes": [empty_route]})
        )
        cache.get_json.return_value = None

        await ors_svc.preview_route(
            origin_lat=13.0, origin_lon=12.0,
            destination_lat=13.1, destination_lon=12.1,
            alternatives=0,
        )

        body = ors_svc._client.post.call_args[1]["json"]
        assert "alternative_routes" not in body
        assert body["coordinates"] == [[12.0, 13.0], [12.1, 13.1]]

    # 13 — ORS body with 2 alternatives (default)
    @pytest.mark.asyncio
    async def test_ors_body_with_alternatives(self, ors_svc, cache):
        ors_svc._client.post = AsyncMock(
            return_value=_mock_http_200(_ORS_RESPONSE)
        )
        cache.get_json.return_value = None

        await ors_svc.preview_route(
            origin_lat=13.0, origin_lon=12.0,
            destination_lat=13.1, destination_lon=12.1,
            alternatives=2,
        )

        body = ors_svc._client.post.call_args[1]["json"]
        assert body["alternative_routes"] == {
            "target_count": 2,
            "weight_factor": 1.4,
        }

    # 13b — clamp alternatives > 2 → 2
    @pytest.mark.asyncio
    async def test_ors_body_clamps_alternatives_above_max(self, ors_svc, cache):
        ors_svc._client.post = AsyncMock(
            return_value=_mock_http_200(_ORS_RESPONSE)
        )
        cache.get_json.return_value = None

        await ors_svc.preview_route(
            origin_lat=13.0, origin_lon=12.0,
            destination_lat=13.1, destination_lon=12.1,
            alternatives=99,
        )

        body = ors_svc._client.post.call_args[1]["json"]
        assert body["alternative_routes"]["target_count"] == 2

    # 13c — negative alternatives clamped to 0
    @pytest.mark.asyncio
    async def test_ors_body_clamps_alternatives_below_min(self, ors_svc, cache):
        ors_svc._client.post = AsyncMock(
            return_value=_mock_http_200(_ORS_RESPONSE)
        )
        cache.get_json.return_value = None

        await ors_svc.preview_route(
            origin_lat=13.0, origin_lon=12.0,
            destination_lat=13.1, destination_lon=12.1,
            alternatives=-5,
        )

        body = ors_svc._client.post.call_args[1]["json"]
        assert "alternative_routes" not in body

    # 14 — different profiles
    @pytest.mark.asyncio
    async def test_ors_body_with_cycling_profile(self, ors_svc, cache):
        route = {
            "geometry": {"coordinates": [[12.0, 13.0], [12.1, 13.1]]},
            "summary": {"distance": 500.0, "duration": 120.0},
            "segments": [],
        }
        ors_svc._client.post = AsyncMock(
            return_value=_mock_http_200({"routes": [route]})
        )
        cache.get_json.return_value = None

        result = await ors_svc.preview_route(
            origin_lat=13.0, origin_lon=12.0,
            destination_lat=13.1, destination_lon=12.1,
            profile="cycling-regular",
        )

        assert result.profile == "cycling-regular"
        assert "cycling-regular" in ors_svc._client.post.call_args[0][0]

    @pytest.mark.asyncio
    async def test_ors_body_with_foot_profile(self, ors_svc, cache):
        route = {
            "geometry": {"coordinates": [[12.0, 13.0], [12.1, 13.1]]},
            "summary": {"distance": 300.0, "duration": 200.0},
            "segments": [],
        }
        ors_svc._client.post = AsyncMock(
            return_value=_mock_http_200({"routes": [route]})
        )
        cache.get_json.return_value = None

        result = await ors_svc.preview_route(
            origin_lat=13.0, origin_lon=12.0,
            destination_lat=13.1, destination_lon=12.1,
            profile="foot-walking",
        )

        assert result.profile == "foot-walking"
        assert "foot-walking" in ors_svc._client.post.call_args[0][0]

    # ---- OSRM (no API key) ----

    # OSRM success
    @pytest.mark.asyncio
    async def test_osrm_success(self, osrm_svc, cache):
        osrm_route = {
            "geometry": {
                "coordinates": [[12.0, 13.0], [12.05, 13.03], [12.1, 13.1]],
            },
            "distance": 15000.0,
            "duration": 900.0,
            "legs": [
                {
                    "steps": [
                        {
                            "distance": 5000.0,
                            "duration": 300.0,
                            "name": "Main St",
                            "maneuver": {"type": "depart", "modifier": "right"},
                        },
                    ]
                }
            ],
        }
        osrm_svc._client.get = AsyncMock(
            return_value=_mock_http_200({"routes": [osrm_route]})
        )
        cache.get_json.return_value = None

        result = await osrm_svc.preview_route(
            origin_lat=13.0, origin_lon=12.0,
            destination_lat=13.1, destination_lon=12.1,
        )

        assert result.provider == "osrm"
        assert result.distance_meters == 15000.0
        assert result.duration_seconds == 900.0
        assert len(result.path) == 3
        assert len(result.steps) == 1
        assert "OSRM" in result.warnings[0]
        assert result.selected_route_id == "route-1"

        osrm_svc._client.get.assert_called_once()
        url = osrm_svc._client.get.call_args[0][0]
        assert "router.project-osrm.org" in url

    # OSRM HTTP error
    @pytest.mark.asyncio
    async def test_osrm_http_error(self, osrm_svc, cache):
        resp = MagicMock(spec=httpx.Response)
        resp.status_code = 429
        resp.json.return_value = {}
        osrm_svc._client.get = AsyncMock(return_value=resp)
        cache.get_json.return_value = None

        with pytest.raises(ExternalServiceError, match="rate limit"):
            await osrm_svc.preview_route(
                origin_lat=13.0, origin_lon=12.0,
                destination_lat=13.1, destination_lon=12.1,
            )

    # OSRM timeout
    @pytest.mark.asyncio
    async def test_osrm_http_exception(self, osrm_svc, cache):
        osrm_svc._client.get = AsyncMock(
            side_effect=httpx.TransportError("connection refused")
        )
        cache.get_json.return_value = None

        with pytest.raises(ExternalServiceError, match="Unable to reach OSRM"):
            await osrm_svc.preview_route(
                origin_lat=13.0, origin_lon=12.0,
                destination_lat=13.1, destination_lon=12.1,
            )

    # OSRM empty routes
    @pytest.mark.asyncio
    async def test_osrm_empty_routes(self, osrm_svc, cache):
        osrm_svc._client.get = AsyncMock(
            return_value=_mock_http_200({"routes": []})
        )
        cache.get_json.return_value = None

        with pytest.raises(ExternalServiceError, match="no route"):
            await osrm_svc.preview_route(
                origin_lat=13.0, origin_lon=12.0,
                destination_lat=13.1, destination_lon=12.1,
            )

    # OSRM with alternatives param
    @pytest.mark.asyncio
    async def test_osrm_body_with_alternatives(self, osrm_svc, cache):
        route = {
            "geometry": {"coordinates": [[12.0, 13.0], [12.1, 13.1]]},
            "distance": 1000.0,
            "duration": 60.0,
            "legs": [],
        }
        osrm_svc._client.get = AsyncMock(
            return_value=_mock_http_200({"routes": [route]})
        )
        cache.get_json.return_value = None

        await osrm_svc.preview_route(
            origin_lat=13.0, origin_lon=12.0,
            destination_lat=13.1, destination_lon=12.1,
            alternatives=1,
        )

        params = osrm_svc._client.get.call_args[1]["params"]
        assert params["alternatives"] == "1"


# ===================================================================
# 15-17 — _normalize_ors_route  (parse ORS response internals)
# ===================================================================

class TestNormalizeORS:
    @pytest.mark.asyncio
    async def test_with_instructions(self, settings, cache):
        svc = RoutingService(settings, cache)
        data = {
            "geometry": {"coordinates": [[12.0, 13.0], [12.1, 13.1]]},
            "summary": {"distance": 5000.0, "duration": 300.0},
            "segments": [
                {
                    "steps": [
                        {
                            "instruction": "Turn left",
                            "distance": 2000.0,
                            "duration": 120.0,
                            "name": "Elm St",
                        },
                        {
                            "instruction": "Turn right",
                            "distance": 3000.0,
                            "duration": 180.0,
                            "name": "Pine Ave",
                        },
                    ]
                }
            ],
        }

        route = svc._normalize_ors_route(data, index=1)

        assert isinstance(route, RouteOption)
        assert route.route_id == "route-1"
        assert route.label == "Primary route"
        assert route.distance_meters == 5000.0
        assert route.duration_seconds == 300.0
        assert len(route.path) == 2
        assert len(route.steps) == 2
        assert route.steps[0].instruction == "Turn left"
        assert route.steps[0].street_name == "Elm St"
        assert route.steps[1].instruction == "Turn right"
        assert route.steps[1].street_name == "Pine Ave"
        assert route.bounds.south == 13.0
        assert route.bounds.north == 13.1

    @pytest.mark.asyncio
    async def test_without_instructions(self, settings, cache):
        svc = RoutingService(settings, cache)
        data = {
            "geometry": {"coordinates": [[12.0, 13.0], [12.1, 13.1]]},
            "summary": {"distance": 2000.0, "duration": 120.0},
            "segments": [],
        }

        route = svc._normalize_ors_route(data, index=2)

        assert route.route_id == "route-2"
        assert route.label == "Alternative 1"
        assert route.distance_meters == 2000.0
        assert route.duration_seconds == 120.0
        assert route.steps == []

    @pytest.mark.asyncio
    async def test_with_polyline_geometry(self, settings, cache):
        svc = RoutingService(settings, cache)
        data = {
            "geometry": "??AA",
            "summary": {"distance": 3000.0, "duration": 180.0},
            "segments": [],
        }

        route = svc._normalize_ors_route(data, index=1)

        assert route.distance_meters == 3000.0
        assert len(route.path) == 2
        assert route.path[0].lat == 0.0
        assert route.path[0].lon == 0.0
        assert abs(route.path[1].lat - 0.00001) < 1e-9
        assert abs(route.path[1].lon - 0.00001) < 1e-9

    @pytest.mark.asyncio
    async def test_empty_polyline_geometry_raises(self, settings, cache):
        svc = RoutingService(settings, cache)
        data = {
            "geometry": "??",
            "summary": {"distance": 100.0, "duration": 10.0},
            "segments": [],
        }

        with pytest.raises(ExternalServiceError, match="invalid route geometry"):
            svc._normalize_ors_route(data, index=1)

    @pytest.mark.asyncio
    async def test_invalid_polyline_lat_triggers_except(self, settings, cache):
        svc = RoutingService(settings, cache)
        # '??_uybQ?' decodes to [(0.0, 0.0), (95.0, 0.0)] — lat=95 > 90 triggers Pydantic ValueError
        data = {
            "geometry": "??_uybQ?",
            "summary": {"distance": 100.0, "duration": 10.0},
            "segments": [],
        }

        with pytest.raises(ExternalServiceError, match="invalid route geometry"):
            svc._normalize_ors_route(data, index=1)

    @pytest.mark.asyncio
    async def test_empty_coordinates_raises(self, settings, cache):
        svc = RoutingService(settings, cache)
        data = {
            "geometry": {"coordinates": [[12.0, 13.0]]},
            "summary": {"distance": 100.0, "duration": 10.0},
            "segments": [],
        }

        with pytest.raises(ExternalServiceError, match="invalid route geometry"):
            svc._normalize_ors_route(data, index=1)

    @pytest.mark.asyncio
    async def test_invalid_coordinate_skipped(self, settings, cache):
        svc = RoutingService(settings, cache)
        data = {
            "geometry": {
                "coordinates": [
                    [12.0, 13.0],
                    ["bad", "data"],
                    [12.1, 13.1],
                ]
            },
            "summary": {"distance": 4000.0, "duration": 240.0},
            "segments": [],
        }

        route = svc._normalize_ors_route(data, index=1)
        # bad coordinate skipped; path = [valid, valid]
        assert len(route.path) == 2
        assert route.path[0].lat == 13.0
        assert route.path[1].lat == 13.1

    @pytest.mark.asyncio
    async def test_missing_segments_key(self, settings, cache):
        svc = RoutingService(settings, cache)
        data = {
            "geometry": {"coordinates": [[12.0, 13.0], [12.1, 13.1]]},
            "summary": {"distance": 1000.0, "duration": 60.0},
        }

        route = svc._normalize_ors_route(data, index=1)
        assert route.steps == []

    @pytest.mark.asyncio
    async def test_multiple_alternatives_labels(self, settings, cache):
        svc = RoutingService(settings, cache)
        data = {
            "geometry": {"coordinates": [[12.0, 13.0], [12.1, 13.1]]},
            "summary": {"distance": 1000.0, "duration": 60.0},
            "segments": [],
        }

        r1 = svc._normalize_ors_route(data, index=1)
        r2 = svc._normalize_ors_route(data, index=2)
        r3 = svc._normalize_ors_route(data, index=3)

        assert r1.label == "Primary route"
        assert r2.label == "Alternative 1"
        assert r3.label == "Alternative 2"


# ===================================================================
# _normalize_osrm_route
# ===================================================================

class TestNormalizeOSRM:
    @pytest.mark.asyncio
    async def test_geojson_geometry_with_steps(self, settings, cache):
        svc = RoutingService(settings, cache)
        data = {
            "geometry": {"coordinates": [[12.0, 13.0], [12.1, 13.1]]},
            "distance": 8000.0,
            "duration": 480.0,
            "legs": [
                {
                    "steps": [
                        {
                            "distance": 3000.0,
                            "duration": 180.0,
                            "name": "High St",
                            "maneuver": {"type": "turn", "modifier": "left"},
                        },
                    ]
                }
            ],
        }

        route = svc._normalize_osrm_route(data, index=1)

        assert route.route_id == "route-1"
        assert route.distance_meters == 8000.0
        assert route.duration_seconds == 480.0
        assert len(route.path) == 2
        assert len(route.steps) == 1
        assert route.steps[0].instruction == "turn left on High St"
        assert route.steps[0].street_name == "High St"

    @pytest.mark.asyncio
    async def test_geojson_invalid_coord_triggers_except(self, settings, cache):
        svc = RoutingService(settings, cache)
        data = {
            "geometry": {
                "coordinates": [
                    [12.0, 200.0],  # lat=200 > 90 → Pydantic ValueError
                    [12.1, 13.1],
                ]
            },
            "distance": 1000.0,
            "duration": 60.0,
            "legs": [],
        }

        with pytest.raises(ExternalServiceError, match="invalid path"):
            svc._normalize_osrm_route(data, index=1)
        svc = RoutingService(settings, cache)
        data = {
            "geometry": {"coordinates": [[12.0, 13.0], [12.1, 13.1]]},
            "distance": 8000.0,
            "duration": 480.0,
            "legs": [
                {
                    "steps": [
                        {
                            "distance": 3000.0,
                            "duration": 180.0,
                            "name": "High St",
                            "maneuver": {"type": "turn", "modifier": "left"},
                        },
                    ]
                }
            ],
        }

        route = svc._normalize_osrm_route(data, index=1)

        assert route.route_id == "route-1"
        assert route.distance_meters == 8000.0
        assert route.duration_seconds == 480.0
        assert len(route.path) == 2
        assert len(route.steps) == 1
        assert route.steps[0].instruction == "turn left on High St"
        assert route.steps[0].street_name == "High St"

    @pytest.mark.asyncio
    async def test_step_maneuver_fallback(self, settings, cache):
        svc = RoutingService(settings, cache)
        # No geometry key — falls back to step manoeuvre locations
        data = {
            "distance": 5000.0,
            "duration": 300.0,
            "legs": [
                {
                    "steps": [
                        {
                            "maneuver": {"type": "depart", "location": [12.0, 13.0]},
                            "distance": 2500.0,
                            "duration": 150.0,
                            "name": "First St",
                        },
                        {
                            "maneuver": {"type": "turn", "location": [12.1, 13.1]},
                            "distance": 2500.0,
                            "duration": 150.0,
                            "name": "Second St",
                        },
                    ]
                }
            ],
        }

        route = svc._normalize_osrm_route(data, index=1)

        assert len(route.path) == 2
        assert route.path[0].lat == 13.0
        assert route.path[0].lon == 12.0

    @pytest.mark.asyncio
    async def test_no_maneuver_location_falls_through(self, settings, cache):
        svc = RoutingService(settings, cache)
        data = {
            "distance": 1000.0,
            "duration": 60.0,
            "legs": [
                {
                    "steps": [
                        {"distance": 1000.0, "duration": 60.0, "name": ""},
                    ]
                }
            ],
        }

        with pytest.raises(ExternalServiceError, match="invalid path"):
            svc._normalize_osrm_route(data, index=1)

    @pytest.mark.asyncio
    async def test_partial_maneuver_location_skipped(self, settings, cache):
        svc = RoutingService(settings, cache)
        data = {
            "distance": 2000.0,
            "duration": 120.0,
            "legs": [
                {
                    "steps": [
                        {
                            "maneuver": {"location": [12.0, 13.0]},
                            "distance": 1000.0, "duration": 60.0, "name": "",
                        },
                        {
                            "maneuver": {"location": [12.1, 13.1]},
                            "distance": 1000.0, "duration": 60.0, "name": "",
                        },
                    ]
                }
            ],
        }

        route = svc._normalize_osrm_route(data, index=1)
        assert len(route.path) == 2

    @pytest.mark.asyncio
    async def test_invalid_maneuver_location_skipped(self, settings, cache):
        svc = RoutingService(settings, cache)
        data = {
            "distance": 3000.0,
            "duration": 180.0,
            "legs": [
                {
                    "steps": [
                        {
                            "maneuver": {"type": "depart", "location": [12.0, 13.0]},
                            "distance": 1000.0, "duration": 60.0, "name": "",
                        },
                        {
                            "maneuver": {"location": ["bad", "data"]},
                            "distance": 1000.0, "duration": 60.0, "name": "",
                        },
                        {
                            "maneuver": {"type": "arrive", "location": [12.1, 13.1]},
                            "distance": 1000.0, "duration": 60.0, "name": "",
                        },
                    ]
                }
            ],
        }

        route = svc._normalize_osrm_route(data, index=1)
        # bad coordinate skipped; first + third give 2 path points
        assert len(route.path) == 2

    @pytest.mark.asyncio
    async def test_empty_geometry_raises(self, settings, cache):
        svc = RoutingService(settings, cache)
        data = {
            "distance": 1000.0,
            "duration": 60.0,
            "legs": [],
        }

        with pytest.raises(ExternalServiceError, match="invalid path"):
            svc._normalize_osrm_route(data, index=1)

    @pytest.mark.asyncio
    async def test_step_without_modifier(self, settings, cache):
        svc = RoutingService(settings, cache)
        data = {
            "geometry": {"coordinates": [[12.0, 13.0], [12.1, 13.1]]},
            "distance": 1000.0,
            "duration": 60.0,
            "legs": [
                {
                    "steps": [
                        {
                            "distance": 1000.0,
                            "duration": 60.0,
                            "name": "Broadway",
                            "maneuver": {"type": "arrive"},
                        },
                    ]
                }
            ],
        }

        route = svc._normalize_osrm_route(data, index=1)
        assert route.steps[0].instruction == "arrive on Broadway"


# ===================================================================
# _build_bounds
# ===================================================================

class TestBuildBounds:
    @pytest.mark.asyncio
    async def test_build_bounds_from_path(self, settings, cache):
        svc = RoutingService(settings, cache)
        path = [
            RoutePoint(lat=13.0, lon=12.0),
            RoutePoint(lat=13.5, lon=12.8),
            RoutePoint(lat=13.2, lon=12.3),
        ]

        bounds = svc._build_bounds(path)

        assert isinstance(bounds, RouteBounds)
        assert bounds.south == 13.0
        assert bounds.north == 13.5
        assert bounds.west == 12.0
        assert bounds.east == 12.8


# ===================================================================
# _decode_polyline
# ===================================================================

class TestDecodePolyline:
    @pytest.mark.asyncio
    async def test_decode_known_encoded_string(self, settings, cache):
        svc = RoutingService(settings, cache)
        # "??AA" decodes to [(0.0, 0.0), (0.00001, 0.00001)]
        result = svc._decode_polyline("??AA")
        assert len(result) == 2
        assert result[0] == (0.0, 0.0)
        assert abs(result[1][0] - 0.00001) < 1e-9
        assert abs(result[1][1] - 0.00001) < 1e-9


# ===================================================================
# _message_from_response
# ===================================================================

class TestMessageFromResponse:
    @pytest.mark.asyncio
    async def test_json_error_dict_message(self, settings, cache):
        svc = RoutingService(settings, cache)
        resp = MagicMock(spec=httpx.Response)
        resp.json.return_value = {"error": {"message": "Quota exceeded"}}
        resp.status_code = 403
        msg = svc._message_from_response(resp)
        assert msg == "Quota exceeded"

    @pytest.mark.asyncio
    async def test_json_error_string_message(self, settings, cache):
        svc = RoutingService(settings, cache)
        resp = MagicMock(spec=httpx.Response)
        resp.json.return_value = {"error": "Invalid API key"}
        resp.status_code = 401
        msg = svc._message_from_response(resp)
        assert msg == "Invalid API key"

    @pytest.mark.asyncio
    async def test_json_message_field(self, settings, cache):
        svc = RoutingService(settings, cache)
        resp = MagicMock(spec=httpx.Response)
        resp.json.return_value = {"message": "Service unavailable"}
        resp.status_code = 503
        msg = svc._message_from_response(resp)
        assert msg == "Service unavailable"

    @pytest.mark.asyncio
    async def test_no_json_returns_generic_message(self, settings, cache):
        svc = RoutingService(settings, cache)
        resp = MagicMock(spec=httpx.Response)
        resp.json.side_effect = ValueError("No JSON")
        resp.status_code = 500
        msg = svc._message_from_response(resp)
        assert msg == "Routing provider could not generate a route right now."

    @pytest.mark.asyncio
    async def test_rate_limit_no_json(self, settings, cache):
        svc = RoutingService(settings, cache)
        resp = MagicMock(spec=httpx.Response)
        resp.json.side_effect = ValueError("No JSON")
        resp.status_code = 429
        msg = svc._message_from_response(resp)
        assert msg == "Routing provider rate limit reached. Please try again in a moment."

    @pytest.mark.asyncio
    async def test_empty_error_string(self, settings, cache):
        svc = RoutingService(settings, cache)
        resp = MagicMock(spec=httpx.Response)
        resp.json.return_value = {"error": ""}
        resp.status_code = 500
        msg = svc._message_from_response(resp)
        assert msg == "Routing provider could not generate a route right now."

    @pytest.mark.asyncio
    async def test_non_dict_json(self, settings, cache):
        svc = RoutingService(settings, cache)
        resp = MagicMock(spec=httpx.Response)
        resp.json.return_value = "plain string error"
        resp.status_code = 500
        msg = svc._message_from_response(resp)
        assert msg == "Routing provider could not generate a route right now."
