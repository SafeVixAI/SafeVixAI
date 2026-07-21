# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from services.exceptions import ExternalServiceError, ServiceValidationError
from services.safe_routing import _validate_coords, get_safe_route, is_nighttime


class TestValidateCoords:
    def test_origin_lat_out_of_range_low(self):
        with pytest.raises(ServiceValidationError, match="origin latitude -91 out of range"):
            _validate_coords((-91, 0), (0, 0))

    def test_origin_lon_out_of_range_high(self):
        with pytest.raises(ServiceValidationError, match="origin longitude 181 out of range"):
            _validate_coords((0, 181), (0, 0))

    def test_dest_lat_out_of_range_high(self):
        with pytest.raises(ServiceValidationError, match="dest latitude 91 out of range"):
            _validate_coords((0, 0), (91, 0))

    def test_dest_lon_out_of_range_low(self):
        with pytest.raises(ServiceValidationError, match="dest longitude -181 out of range"):
            _validate_coords((0, 0), (0, -181))

    def test_valid_coords_pass(self):
        _validate_coords((0, 0), (0, 0))


class TestIsNighttime:
    @patch("services.safe_routing.datetime")
    def test_nighttime_8pm(self, mock_dt):
        mock_dt.now.return_value.hour = 20
        assert is_nighttime() is True

    @patch("services.safe_routing.datetime")
    def test_nighttime_midnight(self, mock_dt):
        mock_dt.now.return_value.hour = 0
        assert is_nighttime() is True

    @patch("services.safe_routing.datetime")
    def test_nighttime_6am(self, mock_dt):
        mock_dt.now.return_value.hour = 6
        assert is_nighttime() is True

    @patch("services.safe_routing.datetime")
    def test_daytime_noon(self, mock_dt):
        mock_dt.now.return_value.hour = 12
        assert is_nighttime() is False

    @patch("services.safe_routing.datetime")
    def test_daytime_7pm(self, mock_dt):
        mock_dt.now.return_value.hour = 19
        assert is_nighttime() is False


class TestGetSafeRouteORS:
    ORS_RESPONSE = {
        "routes": [
            {
                "summary": {"distance": 5000.0, "duration": 300.0},
                "geometry": {"type": "LineString", "coordinates": [[0, 0], [1, 1]]},
            }
        ]
    }

    @pytest.fixture
    def ors_response(self):
        resp = MagicMock()
        resp.json.return_value = self.ORS_RESPONSE
        resp.raise_for_status.return_value = None
        return resp

    @pytest.fixture
    def osrm_response(self):
        resp = MagicMock()
        resp.json.return_value = {
            "routes": [{"distance": 5000.0, "duration": 300.0, "geometry": {"type": "LineString"}}]
        }
        resp.raise_for_status.return_value = None
        return resp

    @pytest.mark.asyncio
    async def test_ors_success_no_safety(self, ors_response):
        mock_client = AsyncMock()
        mock_client.post.return_value = ors_response
        mock_client.__aenter__.return_value = mock_client

        with (
            patch("services.safe_routing.os.getenv", return_value="test-ors-key"),
            patch("services.safe_routing.is_nighttime", return_value=False),
            patch("services.safe_routing.httpx.AsyncClient", return_value=mock_client),
        ):
            result = await get_safe_route((12.97, 77.59), (12.93, 77.61))

        assert result["provider"] == "ors_safe"
        assert result["safety_mode"] is False
        assert result["distance_meters"] == 5000.0
        assert result["duration_seconds"] == 300.0
        assert result["geometry"] == {"type": "LineString", "coordinates": [[0, 0], [1, 1]]}
        assert result["note"] == "Standard ORS route"

    @pytest.mark.asyncio
    async def test_ors_safety_mode_avoid_features(self, ors_response):
        mock_client = AsyncMock()
        mock_client.post.return_value = ors_response
        mock_client.__aenter__.return_value = mock_client

        with (
            patch("services.safe_routing.os.getenv", return_value="test-ors-key"),
            patch("services.safe_routing.is_nighttime", return_value=False),
            patch("services.safe_routing.httpx.AsyncClient", return_value=mock_client),
        ):
            result = await get_safe_route((12.97, 77.59), (12.93, 77.61), prefer_safety=True)

        assert result["provider"] == "ors_safe"
        assert result["safety_mode"] is True
        assert result["note"] == "Route optimized for safety — avoids isolated tracks and roads"
        call_args = mock_client.post.call_args
        body = call_args[1]["json"]
        assert "avoid_features" in body["options"]
        assert body["options"]["avoid_features"] == ["tracks", "fords"]

    @pytest.mark.asyncio
    async def test_ors_nighttime_activates_safety(self, ors_response):
        mock_client = AsyncMock()
        mock_client.post.return_value = ors_response
        mock_client.__aenter__.return_value = mock_client

        with (
            patch("services.safe_routing.os.getenv", return_value="test-ors-key"),
            patch("services.safe_routing.is_nighttime", return_value=True),
            patch("services.safe_routing.httpx.AsyncClient", return_value=mock_client),
        ):
            result = await get_safe_route((12.97, 77.59), (12.93, 77.61))

        assert result["safety_mode"] is True
        assert result["note"] == "Route optimized for safety — avoids isolated tracks and roads"

    @pytest.mark.asyncio
    async def test_ors_timeout_falls_back_to_osrm(self, osrm_response):
        ors_client = AsyncMock()
        ors_client.post.side_effect = httpx.TimeoutException("timed out")
        ors_client.__aenter__.return_value = ors_client

        osrm_client = AsyncMock()
        osrm_client.get.return_value = osrm_response
        osrm_client.__aenter__.return_value = osrm_client

        with (
            patch("services.safe_routing.os.getenv", return_value="test-ors-key"),
            patch("services.safe_routing.is_nighttime", return_value=False),
            patch("services.safe_routing.httpx.AsyncClient", side_effect=[ors_client, osrm_client]),
        ):
            result = await get_safe_route((12.97, 77.59), (12.93, 77.61))

        assert result["provider"] == "osrm_fallback"
        assert result["distance_meters"] == 5000.0

    @pytest.mark.asyncio
    async def test_ors_http_error_falls_back_to_osrm(self, osrm_response):
        ors_client = AsyncMock()
        ors_client.post.side_effect = httpx.HTTPError("400 Bad Request")
        ors_client.__aenter__.return_value = ors_client

        osrm_client = AsyncMock()
        osrm_client.get.return_value = osrm_response
        osrm_client.__aenter__.return_value = osrm_client

        with (
            patch("services.safe_routing.os.getenv", return_value="test-ors-key"),
            patch("services.safe_routing.is_nighttime", return_value=False),
            patch("services.safe_routing.httpx.AsyncClient", side_effect=[ors_client, osrm_client]),
        ):
            result = await get_safe_route((12.97, 77.59), (12.93, 77.61))

        assert result["provider"] == "osrm_fallback"
        assert result["distance_meters"] == 5000.0

    @pytest.mark.asyncio
    async def test_ors_missing_routes_key_raises_error(self, ors_response):
        bad_resp = MagicMock()
        bad_resp.json.return_value = {}
        bad_resp.raise_for_status.return_value = None

        mock_client = AsyncMock()
        mock_client.post.return_value = bad_resp
        mock_client.__aenter__.return_value = mock_client

        with (
            patch("services.safe_routing.os.getenv", return_value="test-ors-key"),
            patch("services.safe_routing.is_nighttime", return_value=False),
            patch("services.safe_routing.httpx.AsyncClient", return_value=mock_client),
        ):
            with pytest.raises(ExternalServiceError, match="Invalid response from ORS routing service"):
                await get_safe_route((12.97, 77.59), (12.93, 77.61))

    @pytest.mark.asyncio
    async def test_ors_empty_routes_list_raises_error(self, ors_response):
        bad_resp = MagicMock()
        bad_resp.json.return_value = {"routes": []}
        bad_resp.raise_for_status.return_value = None

        mock_client = AsyncMock()
        mock_client.post.return_value = bad_resp
        mock_client.__aenter__.return_value = mock_client

        with (
            patch("services.safe_routing.os.getenv", return_value="test-ors-key"),
            patch("services.safe_routing.is_nighttime", return_value=False),
            patch("services.safe_routing.httpx.AsyncClient", return_value=mock_client),
        ):
            with pytest.raises(ExternalServiceError, match="Invalid response from ORS routing service"):
                await get_safe_route((12.97, 77.59), (12.93, 77.61))

    @pytest.mark.asyncio
    async def test_ors_route_missing_summary_raises_error(self, ors_response):
        bad_resp = MagicMock()
        bad_resp.json.return_value = {"routes": [{"geometry": {"type": "LineString"}}]}
        bad_resp.raise_for_status.return_value = None

        mock_client = AsyncMock()
        mock_client.post.return_value = bad_resp
        mock_client.__aenter__.return_value = mock_client

        with (
            patch("services.safe_routing.os.getenv", return_value="test-ors-key"),
            patch("services.safe_routing.is_nighttime", return_value=False),
            patch("services.safe_routing.httpx.AsyncClient", return_value=mock_client),
        ):
            with pytest.raises(ExternalServiceError, match="Invalid response from ORS routing service"):
                await get_safe_route((12.97, 77.59), (12.93, 77.61))


class TestGetSafeRouteOSRM:
    OSRM_RESPONSE = {
        "routes": [{"distance": 6000.0, "duration": 400.0, "geometry": {"type": "LineString"}}]
    }

    @pytest.fixture
    def osrm_response(self):
        resp = MagicMock()
        resp.json.return_value = self.OSRM_RESPONSE
        resp.raise_for_status.return_value = None
        return resp

    @pytest.mark.asyncio
    async def test_osrm_direct_fallback_no_key(self, osrm_response):
        mock_client = AsyncMock()
        mock_client.get.return_value = osrm_response
        mock_client.__aenter__.return_value = mock_client

        with (
            patch("services.safe_routing.os.getenv", return_value=""),
            patch("services.safe_routing.is_nighttime", return_value=True),
            patch("services.safe_routing.httpx.AsyncClient", return_value=mock_client),
        ):
            result = await get_safe_route((12.97, 77.59), (12.93, 77.61))

        assert result["provider"] == "osrm_fallback"
        assert result["safety_mode"] is True
        assert result["distance_meters"] == 6000.0
        assert result["duration_seconds"] == 400.0
        assert result["geometry"] == {"type": "LineString"}
        assert "without ORS key" in result["note"]

    @pytest.mark.asyncio
    async def test_osrm_direct_no_safety_note(self, osrm_response):
        mock_client = AsyncMock()
        mock_client.get.return_value = osrm_response
        mock_client.__aenter__.return_value = mock_client

        with (
            patch("services.safe_routing.os.getenv", return_value=""),
            patch("services.safe_routing.is_nighttime", return_value=False),
            patch("services.safe_routing.httpx.AsyncClient", return_value=mock_client),
        ):
            result = await get_safe_route((12.97, 77.59), (12.93, 77.61))

        assert result["provider"] == "osrm_fallback"
        assert result["safety_mode"] is False
        assert result["note"] == "Standard OSRM route (no ORS key configured)."

    @pytest.mark.asyncio
    async def test_osrm_timeout_raises_error(self):
        mock_client = AsyncMock()
        mock_client.get.side_effect = httpx.TimeoutException("timed out")
        mock_client.__aenter__.return_value = mock_client

        with (
            patch("services.safe_routing.os.getenv", return_value=""),
            patch("services.safe_routing.is_nighttime", return_value=False),
            patch("services.safe_routing.httpx.AsyncClient", return_value=mock_client),
        ):
            with pytest.raises(ExternalServiceError, match="Routing service unavailable"):
                await get_safe_route((12.97, 77.59), (12.93, 77.61))

    @pytest.mark.asyncio
    async def test_osrm_http_error_raises_error(self):
        mock_client = AsyncMock()
        mock_client.get.side_effect = httpx.HTTPError("500 Server Error")
        mock_client.__aenter__.return_value = mock_client

        with (
            patch("services.safe_routing.os.getenv", return_value=""),
            patch("services.safe_routing.is_nighttime", return_value=False),
            patch("services.safe_routing.httpx.AsyncClient", return_value=mock_client),
        ):
            with pytest.raises(ExternalServiceError, match="Routing service unavailable"):
                await get_safe_route((12.97, 77.59), (12.93, 77.61))

    @pytest.mark.asyncio
    async def test_osrm_empty_routes_raises_error(self):
        bad_resp = MagicMock()
        bad_resp.json.return_value = {"routes": []}
        bad_resp.raise_for_status.return_value = None

        mock_client = AsyncMock()
        mock_client.get.return_value = bad_resp
        mock_client.__aenter__.return_value = mock_client

        with (
            patch("services.safe_routing.os.getenv", return_value=""),
            patch("services.safe_routing.is_nighttime", return_value=False),
            patch("services.safe_routing.httpx.AsyncClient", return_value=mock_client),
        ):
            with pytest.raises(ExternalServiceError, match="No route found between the given locations"):
                await get_safe_route((12.97, 77.59), (12.93, 77.61))

    @pytest.mark.asyncio
    async def test_osrm_empty_data_no_routes_key_raises_error(self):
        bad_resp = MagicMock()
        bad_resp.json.return_value = {}
        bad_resp.raise_for_status.return_value = None

        mock_client = AsyncMock()
        mock_client.get.return_value = bad_resp
        mock_client.__aenter__.return_value = mock_client

        with (
            patch("services.safe_routing.os.getenv", return_value=""),
            patch("services.safe_routing.is_nighttime", return_value=False),
            patch("services.safe_routing.httpx.AsyncClient", return_value=mock_client),
        ):
            with pytest.raises(ExternalServiceError, match="No route found between the given locations"):
                await get_safe_route((12.97, 77.59), (12.93, 77.61))
