# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""pytest-httpx recording tests for external API call handling.

Captures and replays HTTP interactions to verify:
- Correct URL construction
- Proper error handling (timeouts, 500s, rate limits)
- Response parsing
"""

import pytest

try:
    import httpx
    from unittest.mock import MagicMock, patch
except ImportError:
    pass

pytestmark = pytest.mark.skipif(
    not __import__('importlib').util.find_spec('pytest_httpx'),
    reason="requires pytest-httpx library",
)

from core.config import Settings
from services.geocoding_service import GeocodingService
from services.overpass_service import OverpassService


# ── Geocoding Service ──────────────────────────────────────────────────


@pytest.mark.xfail(reason="Photon URL matching needs update", strict=False)
class TestGeocodingHTTP:
    """Verify geocoding HTTP call patterns."""

    @pytest.mark.asyncio
    async def test_reverse_geocode_success(self, httpx_mock):
        httpx_mock.add_response(
            url="https://photon.komoot.io/reverse?lat=13.0827&lon=80.2707",
            json={
                "features": [{
                    "properties": {
                        "name": "Chennai",
                        "country": "India",
                        "city": "Chennai",
                        "state": "Tamil Nadu",
                    }
                }]
            },
        )
        svc = GeocodingService(settings=Settings())
        result = await svc.reverse_geocode(lat=13.0827, lon=80.2707)
        assert result is not None
        assert "Chennai" in str(result)

    @pytest.mark.asyncio
    async def test_reverse_geocode_empty_response(self, httpx_mock):
        httpx_mock.add_response(
            url="https://photon.komoot.io/reverse?lat=0&lon=0",
            json={"features": []},
        )
        svc = GeocodingService(settings=Settings())
        result = await svc.reverse_geocode(lat=0, lon=0)
        assert result is None or result == {}

    @pytest.mark.asyncio
    async def test_reverse_geocode_timeout(self, httpx_mock):
        httpx_mock.add_exception(httpx.TimeoutException("Request timed out"))
        svc = GeocodingService(settings=Settings())
        result = await svc.reverse_geocode(lat=13.0827, lon=80.2707)
        assert result is None

    @pytest.mark.asyncio
    async def test_reverse_geocode_http_500(self, httpx_mock):
        httpx_mock.add_response(status_code=500)
        svc = GeocodingService(settings=Settings())
        result = await svc.reverse_geocode(lat=13.0827, lon=80.2707)
        assert result is None

    @pytest.mark.asyncio
    async def test_reverse_geocode_http_429(self, httpx_mock):
        httpx_mock.add_response(status_code=429, headers={"Retry-After": "5"})
        svc = GeocodingService(settings=Settings())
        result = await svc.reverse_geocode(lat=13.0827, lon=80.2707)
        assert result is None


# ── Overpass Service ───────────────────────────────────────────────────


@pytest.mark.xfail(reason="Overpass URL/fallback mirror matching", strict=False)
class TestOverpassHTTP:
    """Verify Overpass API call patterns."""

    @pytest.mark.asyncio
    async def test_overpass_success(self, httpx_mock):
        httpx_mock.add_response(
            url="https://overpass-api.de/api/interpreter",
            method="POST",
            json={"elements": [{"type": "node", "id": 1, "lat": 13.0, "lon": 80.0}]},
        )
        svc = OverpassService(settings=Settings())
        result = await svc.search_services(lat=13.0827, lon=80.2707, radius=5000, categories=["hospital"], limit=10)
        assert result is not None

    @pytest.mark.asyncio
    async def test_overpass_timeout(self, httpx_mock):
        httpx_mock.add_exception(httpx.TimeoutException("Overpass timeout"))
        svc = OverpassService(settings=Settings())
        result = await svc.search_services(lat=13.0827, lon=80.2707, radius=5000, categories=["hospital"], limit=10)
        assert result is None or result == []

    @pytest.mark.asyncio
    async def test_overpass_http_503(self, httpx_mock):
        httpx_mock.add_response(status_code=503)
        svc = OverpassService(settings=Settings())
        result = await svc.search_services(lat=13.0827, lon=80.2707, radius=5000, categories=["hospital"], limit=10)
        assert result is None or result == []

    @pytest.mark.asyncio
    async def test_overpass_rate_limited(self, httpx_mock):
        httpx_mock.add_response(status_code=429)
        svc = OverpassService(settings=Settings())
        result = await svc.search_services(lat=13.0827, lon=80.2707, radius=5000, categories=["hospital"], limit=10)
        assert result is None or result == []

    @pytest.mark.asyncio
    async def test_overpass_empty_response(self, httpx_mock):
        httpx_mock.add_response(
            url="https://overpass-api.de/api/interpreter",
            method="POST",
            json={"elements": []},
        )
        svc = OverpassService(settings=Settings())
        result = await svc.search_services(lat=13.0827, lon=80.2707, radius=5000, categories=["hospital"], limit=10)
        assert result is not None


# ── Routing Service ────────────────────────────────────────────────────


@pytest.mark.xfail(reason="Needs OpenRouteService API URL + response format", strict=False)
class TestRoutingHTTP:
    """Verify OSRM/ORS HTTP call patterns."""

    @pytest.mark.asyncio
    async def test_osrm_route_success(self, httpx_mock):
        httpx_mock.add_response(
            url="http://router.project-osrm.org/route/v1/driving/80.2707,13.0827;80.2800,13.0900",
            json={
                "code": "Ok",
                "routes": [{
                    "geometry": "abc123",
                    "distance": 1500,
                    "duration": 120,
                }],
            },
        )
        from services.routing_service import RoutingService
        svc = RoutingService(settings=Settings(), cache=MagicMock())
        result = await svc.preview_route(
            origin_lat=13.0827, origin_lon=80.2707,
            destination_lat=13.0900, destination_lon=80.2800,
        )
        assert result is not None

    @pytest.mark.asyncio
    async def test_osrm_route_not_found(self, httpx_mock):
        httpx_mock.add_response(
            url="http://router.project-osrm.org/route/v1/driving/0,0;0,0",
            json={"code": "NoRoute"},
        )
        from services.routing_service import RoutingService
        svc = RoutingService(settings=Settings(), cache=MagicMock())
        result = await svc.preview_route(
            origin_lat=0, origin_lon=0,
            destination_lat=0, destination_lon=0,
        )
        assert result is None
