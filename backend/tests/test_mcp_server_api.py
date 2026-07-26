# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""MCP Server API tests for SafeVixAI backend."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from api.v1 import mcp_server

# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_test_env():
    """Patch settings to return test environment."""
    with patch("core.config.get_settings") as mock_settings:
        mock_settings.return_value.environment = "test"
        mock_settings.return_value.redis_url = None
        mock_settings.return_value.max_radius = 25000
        yield mock_settings


@pytest.fixture
def test_client(mock_test_env):
    """Create a test client for the MCP router."""
    from fastapi import FastAPI

    app = FastAPI()

    # Override the dependency to bypass auth in tests
    async def mock_auth():
        return {"sub": "test-user", "role": "admin"}

    app.include_router(mcp_server.router)
    app.dependency_overrides[mcp_server.require_mcp_admin] = mock_auth

    return TestClient(app)


# ── MCP Tool Tests ───────────────────────────────────────────────────────────

class TestGetEmergencyServices:
    """Tests for get_emergency_services MCP tool."""

    @pytest.mark.asyncio
    async def test_valid_coordinates_returns_services(self):
        """Test emergency services lookup with valid coordinates."""
        with patch("core.config.get_settings") as mock_settings, \
             patch("core.redis_client.create_cache") as mock_cache, \
             patch("services.overpass_service.OverpassService") as mock_overpass, \
             patch("services.emergency_locator.EmergencyLocatorService") as mock_locator:

            mock_settings.return_value.environment = "test"
            mock_settings.return_value.redis_url = None
            mock_settings.return_value.max_radius = 25000

            # Mock facility
            mock_facility = MagicMock()
            mock_facility.name = "City Hospital"
            mock_facility.category = "hospital"
            mock_facility.has_trauma = True
            mock_facility.has_icu = False
            mock_facility.is_24hr = True
            mock_facility.distance_meters = 1200.0
            mock_facility.phone_emergency = "108"
            mock_facility.phone = None

            mock_locator.return_value.get_nearby_facilities = AsyncMock(return_value=[mock_facility])
            mock_cache.return_value.close = AsyncMock()
            mock_overpass.return_value.aclose = AsyncMock()

            result = await mcp_server.get_emergency_services(13.0827, 80.2707, radius=5000)

            assert "City Hospital" in result
            assert "trauma" in result
            assert "24hr" in result
            assert "108" in result

    @pytest.mark.asyncio
    async def test_invalid_coordinates_returns_error(self):
        """Test that invalid coordinates return an error message."""
        result = await mcp_server.get_emergency_services(0, 0)
        assert "Invalid coordinates" in result

        result = await mcp_server.get_emergency_services(100, 100)
        assert "Invalid coordinates" in result

    @pytest.mark.asyncio
    async def test_no_services_found_returns_fallback(self):
        """Test fallback message when no services found."""
        with patch("core.config.get_settings") as mock_settings, \
             patch("core.redis_client.create_cache") as mock_cache, \
             patch("services.overpass_service.OverpassService") as mock_overpass, \
             patch("services.emergency_locator.EmergencyLocatorService") as mock_locator:

            mock_settings.return_value.environment = "test"
            mock_settings.return_value.redis_url = None
            mock_settings.return_value.max_radius = 25000

            mock_locator.return_value.get_nearby_facilities = AsyncMock(return_value=[])
            mock_cache.return_value.close = AsyncMock()
            mock_overpass.return_value.aclose = AsyncMock()

            result = await mcp_server.get_emergency_services(13.0827, 80.2707)
            assert "112" in result

    @pytest.mark.asyncio
    async def test_exception_handling(self):
        """Test graceful error handling on service failure."""
        with patch("core.config.get_settings") as mock_settings, \
             patch("core.redis_client.create_cache") as mock_cache, \
             patch("services.overpass_service.OverpassService") as mock_overpass, \
             patch("services.emergency_locator.EmergencyLocatorService") as mock_locator:

            mock_settings.return_value.environment = "test"
            mock_settings.return_value.redis_url = None
            mock_settings.return_value.max_radius = 25000

            mock_locator.return_value.get_nearby_facilities = AsyncMock(side_effect=Exception("Connection failed"))
            mock_cache.return_value.close = AsyncMock()
            mock_overpass.return_value.aclose = AsyncMock()

            result = await mcp_server.get_emergency_services(13.0827, 80.2707)
            assert "Failed to fetch" in result


class TestReportRoadIssue:
    """Tests for report_road_issue MCP tool."""

    @pytest.mark.asyncio
    async def test_valid_report_submission(self):
        """Test successful road issue report."""
        from types import SimpleNamespace
        mock_result = SimpleNamespace(
            uuid="test-uuid-123",
            issue_id="test-uuid-123",
            complaint_ref="CR-2026-001",
        )
        mock_service = AsyncMock()
        mock_service.submit_report = AsyncMock(return_value=mock_result)

        mock_cache = AsyncMock()
        mock_cache.close = AsyncMock()

        mock_overpass = AsyncMock()
        mock_overpass.aclose = AsyncMock()

        mock_geocoding = AsyncMock()
        mock_geocoding.aclose = AsyncMock()

        async def mock_build():
            return (mock_service, mock_cache, mock_overpass, mock_geocoding)

        with patch("api.v1.mcp_server._build_roadwatch_service", new=mock_build), \
             patch("core.database.get_async_session") as mock_session:

            async def mock_gen():
                yield AsyncMock(spec=["execute", "commit", "rollback"])

            mock_session.side_effect = mock_gen

            result = await mcp_server.report_road_issue("pothole", 3, 13.0827, 80.2707, "Large pothole on main road")

            assert "test-uuid-123" in result
            assert "CR-2026-001" in result
            assert "pothole" in result

    @pytest.mark.asyncio
    async def test_invalid_coordinates(self):
        """Test invalid coordinates rejection."""
        result = await mcp_server.report_road_issue("pothole", 3, 0, 0)
        assert "Invalid coordinates" in result

    @pytest.mark.asyncio
    async def test_invalid_severity(self):
        """Test invalid severity rejection."""
        result = await mcp_server.report_road_issue("pothole", 0, 13.0827, 80.2707)
        assert "Invalid severity" in result

        result = await mcp_server.report_road_issue("pothole", 6, 13.0827, 80.2707)
        assert "Invalid severity" in result


class TestCalculateChallan:
    """Tests for calculate_challan MCP tool."""

    @pytest.mark.asyncio
    async def test_known_offense_type(self):
        """Test challan calculation with known offense type."""
        from models.schemas import ChallanResponse

        with patch("core.config.get_settings") as mock_settings, \
             patch("services.challan_service.ChallanService") as mock_service:

            mock_settings.return_value.environment = "test"

            mock_result = ChallanResponse(
                violation_code="185",
                vehicle_class="car",
                state_code="TN",
                base_fine=1000,
                amount_due=1000,
                section="185",
                description="Drunk driving",
                state_override=None,
            )

            mock_service_instance = MagicMock()
            mock_service_instance.calculate = MagicMock(return_value=mock_result)
            mock_service.return_value = mock_service_instance

            result = await mcp_server.calculate_challan("car", "drunk_driving", state_code="TN")

            assert "185" in result
            assert "1000" in result
            assert "Drunk driving" in result

    @pytest.mark.asyncio
    async def test_repeat_offense(self):
        """Test repeat offense pricing."""
        from models.schemas import ChallanResponse

        with patch("core.config.get_settings") as mock_settings, \
             patch("services.challan_service.ChallanService") as mock_service:

            mock_settings.return_value.environment = "test"

            mock_result = ChallanResponse(
                violation_code="183",
                vehicle_class="car",
                state_code="TN",
                base_fine=1000,
                repeat_fine=2000,
                amount_due=2000,
                section="183",
                description="Speeding",
                state_override=None,
            )

            mock_service_instance = MagicMock()
            mock_service_instance.calculate = MagicMock(return_value=mock_result)
            mock_service.return_value = mock_service_instance

            result = await mcp_server.calculate_challan("car", "speeding", previous_offenses=2)

            assert "Repeat offense" in result

    @pytest.mark.asyncio
    async def test_state_override(self):
        """Test state-specific override note."""
        from models.schemas import ChallanResponse

        with patch("core.config.get_settings") as mock_settings, \
             patch("services.challan_service.ChallanService") as mock_service:

            mock_settings.return_value.environment = "test"

            mock_result = ChallanResponse(
                violation_code="179",
                vehicle_class="car",
                state_code="MH",
                base_fine=1500,
                amount_due=1500,
                section="179",
                description="Red light violation",
                state_override="Maharashtra override applied",
            )

            mock_service_instance = MagicMock()
            mock_service_instance.calculate = MagicMock(return_value=mock_result)
            mock_service.return_value = mock_service_instance

            result = await mcp_server.calculate_challan("car", "red_light", state_code="MH")

            assert "Maharashtra override" in result


class TestGetRoadWeather:
    """Tests for get_road_weather MCP tool."""

    @pytest.mark.asyncio
    async def test_clear_weather(self):
        """Test clear weather conditions."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "current": {
                "temperature_2m": 28.5,
                "relative_humidity_2m": 65,
                "precipitation": 0,
                "rain": 0,
                "snowfall": 0,
                "weather_code": 0,
                "wind_speed_10m": 12,
                "visibility": 10000,
            }
        }
        mock_response.raise_for_status = MagicMock()

        with patch("api.v1.mcp_server.httpx.AsyncClient.get", return_value=mock_response):
            result = await mcp_server.get_road_weather(13.0827, 80.2707)
            assert "LOW" in result

    @pytest.mark.asyncio
    async def test_rainy_weather(self):
        """Test rainy weather warnings."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "current": {
                "temperature_2m": 24.0,
                "relative_humidity_2m": 85,
                "precipitation": 8.5,
                "rain": 8.5,
                "snowfall": 0,
                "weather_code": 61,
                "wind_speed_10m": 25,
                "visibility": 2500,
            }
        }
        mock_response.raise_for_status = MagicMock()

        with patch("api.v1.mcp_server.httpx.AsyncClient.get", return_value=mock_response):
            result = await mcp_server.get_road_weather(13.0827, 80.2707)
            assert "HIGH" in result
            assert "wet roads" in result
            assert "reduced visibility" in result

    @pytest.mark.asyncio
    async def test_invalid_coordinates(self):
        """Test invalid coordinates rejection."""
        result = await mcp_server.get_road_weather(0, 0)
        assert "Invalid coordinates" in result


class TestCalculateSafeRoute:
    """Tests for calculate_safe_route MCP tool."""

    @pytest.mark.asyncio
    async def test_valid_route(self):
        """Test successful route calculation."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "routes": [{
                "distance": 12500.0,
                "duration": 1800.0,
                "legs": [{
                    "steps": [
                        {"maneuver": {"type": "depart", "modifier": "right"}, "name": "Main Road"},
                        {"maneuver": {"type": "turn", "modifier": "left"}, "name": "Side Street"},
                    ]
                }]
            }]
        }
        mock_response.raise_for_status = MagicMock()

        with patch("api.v1.mcp_server.httpx.AsyncClient.get", return_value=mock_response):
            result = await mcp_server.calculate_safe_route(13.0827, 80.2707, 13.0900, 80.2800)
            assert "12.5 km" in result
            assert "30 min" in result
            assert "Main Road" in result

    @pytest.mark.asyncio
    async def test_no_route_found(self):
        """Test no route found scenario."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"routes": []}
        mock_response.raise_for_status = MagicMock()

        with patch("api.v1.mcp_server.httpx.AsyncClient.get", return_value=mock_response):
            result = await mcp_server.calculate_safe_route(13.0827, 80.2707, 13.0900, 80.2800)
            assert "No route found" in result

    @pytest.mark.asyncio
    async def test_invalid_coordinates(self):
        """Test invalid coordinates rejection."""
        result = await mcp_server.calculate_safe_route(0, 0, 13.0900, 80.2800)
        assert "Invalid route" in result


class TestGetFirstAidGuide:
    """Tests for get_first_aid_guide MCP tool."""

    @pytest.mark.asyncio
    async def test_bleeding_guide(self):
        """Test first aid guide for bleeding."""
        result = await mcp_server.get_first_aid_guide("bleeding")
        assert "direct pressure" in result.lower()
        assert "108" in result or "112" in result

    @pytest.mark.asyncio
    async def test_unconscious_guide(self):
        """Test first aid guide for unconscious person."""
        result = await mcp_server.get_first_aid_guide("unconscious")
        assert "CPR" in result or "compressions" in result.lower()

    @pytest.mark.asyncio
    async def test_severe_crash_note(self):
        """Test severe crash severity note."""
        result = await mcp_server.get_first_aid_guide("bleeding", crash_severity="severe")
        assert "high priority" in result.lower()

    @pytest.mark.asyncio
    async def test_unknown_injury_falls_back_to_bleeding(self):
        """Test unknown injury type falls back to bleeding guide."""
        result = await mcp_server.get_first_aid_guide("unknown_injury")
        assert "direct pressure" in result.lower()


class TestGetLocationFromWhat3Words:
    """Tests for get_location_from_what3words MCP tool."""

    @pytest.mark.asyncio
    async def test_valid_what3words_address(self):
        """Test valid What3Words address conversion."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "coordinates": {"lat": 51.5208, "lng": -0.1955}
        }
        mock_response.raise_for_status = MagicMock()

        with patch("core.config.get_settings") as mock_settings, \
             patch("api.v1.mcp_server.httpx.AsyncClient.get", return_value=mock_response):

            mock_settings.return_value.w3w_api_key = "test-key"

            result = await mcp_server.get_location_from_what3words("filled.count.soap")
            assert "51.5208" in result
            assert "-0.1955" in result

    @pytest.mark.asyncio
    async def test_invalid_what3words_format(self):
        """Test invalid What3Words format rejection."""
        result = await mcp_server.get_location_from_what3words("invalid words")
        assert "Invalid What3Words" in result

    @pytest.mark.asyncio
    async def test_missing_api_key(self):
        """Test missing API key handling."""
        with patch("core.config.get_settings") as mock_settings:
            mock_settings.return_value.w3w_api_key = None

            result = await mcp_server.get_location_from_what3words("filled.count.soap")
            assert "API key is not configured" in result


# ── MCP Info Endpoint Tests ─────────────────────────────────────────────────

class TestMCPInfoEndpoint:
    """Tests for the MCP info REST endpoint."""

    def test_get_mcp_info_returns_metadata(self, test_client):
        """Test MCP info endpoint returns server metadata."""
        response = test_client.get("/mcp_info/")
        assert response.status_code == 200

        data = response.json()
        assert data["service"] == "SafeVixAI MCP Server"
        assert "tools" in data
        assert len(data["tools"]) == 7
        assert "get_emergency_services" in data["tools"]
        assert "calculate_challan" in data["tools"]
        assert "get_first_aid_guide" in data["tools"]

    def test_mcp_info_rate_limit_info(self, test_client):
        """Test rate limit information in MCP info."""
        response = test_client.get("/mcp_info/")
        data = response.json()

        assert "rate_limit" in data
        assert "10 requests per 60s" in data["rate_limit"]

    def test_mcp_info_auth_info(self, test_client):
        """Test authentication info in MCP info."""
        response = test_client.get("/mcp_info/")
        data = response.json()

        assert "auth" in data
        assert "Admin or Operator" in data["auth"]


# ── Utility Function Tests ──────────────────────────────────────────────────

class TestUtilityFunctions:
    """Tests for MCP utility functions."""

    def test_valid_lat_lon(self):
        """Test coordinate validation function."""
        assert mcp_server._valid_lat_lon(13.0827, 80.2707) is True
        assert mcp_server._valid_lat_lon(-90, -180) is True
        assert mcp_server._valid_lat_lon(90, 180) is True

    def test_invalid_lat_lon_zero(self):
        """Test that 0,0 coordinates are rejected."""
        assert mcp_server._valid_lat_lon(0, 0) is False

    def test_invalid_lat_lon_out_of_range(self):
        """Test out-of-range coordinates are rejected."""
        assert mcp_server._valid_lat_lon(100, 80) is False
        assert mcp_server._valid_lat_lon(13, 200) is False
        assert mcp_server._valid_lat_lon(-91, 80) is False

    def test_rate_limit_logic(self):
        """Test rate limiting logic."""

        # Reset rate store
        mcp_server._rate_store.clear()

        # Create mock request
        mock_request = MagicMock()
        mock_request.client.host = "127.0.0.1"

        # First request should pass
        assert mcp_server._check_mcp_rate_limit(mock_request) is True

        # Fill up the rate limit
        for _ in range(9):
            mcp_server._check_mcp_rate_limit(mock_request)

        # 11th request should fail
        assert mcp_server._check_mcp_rate_limit(mock_request) is False

    def test_auth_middleware_test_environment(self):
        """Test auth middleware allows all requests in test environment."""
        with patch("core.config.get_settings") as mock_settings:
            mock_settings.return_value.environment = "test"

            mock_request = MagicMock()
            mock_request.client.host = "127.0.0.1"

            assert mcp_server._check_mcp_auth(mock_request) is True
