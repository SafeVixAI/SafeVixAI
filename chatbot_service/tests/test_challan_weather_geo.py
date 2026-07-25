# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from config import Settings
from tools import BackendToolClient
from tools.challan_tool import ChallanTool
from tools.geocoding import GeocodingClient
from tools.open_meteo import OpenMeteoClient
from tools.weather_tool import WeatherTool

# ===================================================================
# Helpers
# ===================================================================

def _make_weather_settings(**overrides: str | None) -> MagicMock:
    s = MagicMock(spec=Settings)
    s.http_timeout_seconds = 20.0
    s.http_user_agent = "SafeVixAIChatbot/1.0"
    s.openweather_api_key = "test-owm-key"
    s.openweather_base_url = "https://api.openweathermap.org/data/2.5"
    s.openweather_units = "metric"
    for k, v in overrides.items():
        setattr(s, k, v)
    return s


# ===================================================================
# ChallanTool
# ===================================================================

class TestChallanTool:

    def test_constructor_stores_backend_client(self):
        backend = MagicMock(spec=BackendToolClient)
        tool = ChallanTool(backend_client=backend)
        assert tool.backend_client is backend

    @pytest.mark.asyncio
    async def test_calculate_success_returns_dict(self):
        backend = AsyncMock(spec=BackendToolClient)
        backend.post.return_value = {"fine": 5000, "violation": "185"}
        tool = ChallanTool(backend_client=backend)

        result = await tool.calculate(
            violation_code="185",
            vehicle_class="light_motor_vehicle",
            state_code="TN",
            is_repeat=False,
        )

        assert result == {"fine": 5000, "violation": "185"}
        backend.post.assert_awaited_once_with(
            '/api/v1/challan/calculate',
            payload={
                'violation_code': '185',
                'vehicle_class': 'light_motor_vehicle',
                'state_code': 'TN',
                'is_repeat': False,
            },
        )

    @pytest.mark.asyncio
    async def test_calculate_backend_fails_returns_none(self):
        backend = AsyncMock(spec=BackendToolClient)
        backend.post.return_value = None
        tool = ChallanTool(backend_client=backend)

        result = await tool.calculate(
            violation_code="185",
            vehicle_class="car",
            state_code="KA",
            is_repeat=True,
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_infer_and_calculate_violation_and_state_in_message(self):
        backend = AsyncMock(spec=BackendToolClient)
        backend.post.return_value = {"fine": 5000}
        tool = ChallanTool(backend_client=backend)

        result = await tool.infer_and_calculate("I was speeding 185 in TN")

        assert result == {"fine": 5000}
        backend.post.assert_awaited_once_with(
            '/api/v1/challan/calculate',
            payload={
                'violation_code': '185',
                'vehicle_class': 'light_motor_vehicle',
                'state_code': 'TN',
                'is_repeat': False,
            },
        )

    @pytest.mark.asyncio
    async def test_infer_and_calculate_no_state_code_uses_ip_fallback(self):
        backend = AsyncMock(spec=BackendToolClient)
        backend.post.return_value = {"fine": 10000}
        tool = ChallanTool(backend_client=backend)

        with patch('tools.challan_tool.detect_state_from_ip', AsyncMock(return_value={"state": "Karnataka"})):
            result = await tool.infer_and_calculate("I was speeding 185", client_ip="1.2.3.4")

        assert result == {"fine": 10000}
        backend.post.assert_awaited_once_with(
            '/api/v1/challan/calculate',
            payload={
                'violation_code': '185',
                'vehicle_class': 'light_motor_vehicle',
                'state_code': 'KA',
                'is_repeat': False,
            },
        )

    @pytest.mark.asyncio
    async def test_infer_and_calculate_no_violation_returns_none(self):
        backend = AsyncMock(spec=BackendToolClient)
        tool = ChallanTool(backend_client=backend)

        result = await tool.infer_and_calculate("How are you doing today?")

        assert result is None
        backend.post.assert_not_awaited()

    @pytest.mark.parametrize("message", [
        "I was speeding 185 in TN second time",
        "I got caught for 185 again",
        "This is a repeat offense 183 in MH",
    ])
    @pytest.mark.asyncio
    async def test_infer_and_calculate_repeat_detection(self, message: str):
        backend = AsyncMock(spec=BackendToolClient)
        backend.post.return_value = {"fine": 10000}
        tool = ChallanTool(backend_client=backend)

        result = await tool.infer_and_calculate(message)

        assert result is not None
        call_payload = backend.post.await_args.kwargs['payload']
        assert call_payload['is_repeat'] is True

    @pytest.mark.parametrize("message,expected_class", [
        ("I was riding a bike", "two_wheeler"),
        ("motorcycle overspeeding", "two_wheeler"),
        ("scooter accident", "two_wheeler"),
        ("2w violation 185", "two_wheeler"),
        ("truck overloading 179", "heavy_vehicle"),
        ("lorry hit me 181", "heavy_vehicle"),
        ("htv overspeeding", "heavy_vehicle"),
        ("bus violation 183", "bus"),
        ("commercial bus overloading", "bus"),
        ("comm vehicle challan", "bus"),
        ("car overspeeding 185", "light_motor_vehicle"),
        ("I was driving an SUV", "light_motor_vehicle"),
    ])
    def test_infer_vehicle_class(self, message: str, expected_class: str):
        assert ChallanTool._infer_vehicle_class(message) == expected_class

    @pytest.mark.asyncio
    async def test_infer_and_calculate_ip_state_fallback_default_tn(self):
        backend = AsyncMock(spec=BackendToolClient)
        backend.post.return_value = {"fine": 5000}
        tool = ChallanTool(backend_client=backend)

        with patch('tools.challan_tool.detect_state_from_ip', AsyncMock(return_value={"state": "Unknown"})):
            result = await tool.infer_and_calculate("speeding 185", client_ip="9.9.9.9")

        assert result == {"fine": 5000}
        call_payload = backend.post.await_args.kwargs['payload']
        assert call_payload['state_code'] == 'TN'

    @pytest.mark.asyncio
    async def test_state_to_code_mapping_tamil_nadu(self):
        backend = AsyncMock(spec=BackendToolClient)
        backend.post.return_value = {"fine": 5000}
        tool = ChallanTool(backend_client=backend)

        with patch('tools.challan_tool.detect_state_from_ip', AsyncMock(return_value={"state": "Tamil Nadu"})):
            result = await tool.infer_and_calculate("speeding 185", client_ip="1.2.3.4")

        assert result is not None
        call_payload = backend.post.await_args.kwargs['payload']
        assert call_payload['state_code'] == 'TN'

    @pytest.mark.asyncio
    async def test_infer_and_calculate_vehicle_class_inference(self):
        backend = AsyncMock(spec=BackendToolClient)
        backend.post.return_value = {"fine": 3000}
        tool = ChallanTool(backend_client=backend)

        result = await tool.infer_and_calculate("truck overspeeding 179 in DL")

        assert result == {"fine": 3000}
        call_payload = backend.post.await_args.kwargs['payload']
        assert call_payload['vehicle_class'] == 'heavy_vehicle'
        assert call_payload['state_code'] == 'DL'
        assert call_payload['violation_code'] == '179'


# ===================================================================
# WeatherTool
# ===================================================================

class TestWeatherTool:

    def test_constructor_creates_open_meteo_and_owm_clients(self):
        settings = _make_weather_settings()
        with patch('tools.weather_tool.OpenMeteoClient') as mock_om_cls, \
             patch('tools.weather_tool.httpx.AsyncClient') as mock_http_cls:
            WeatherTool(settings)
            mock_om_cls.assert_called_once_with(settings)
            mock_http_cls.assert_called_once_with(
                timeout=20.0,
                headers={'User-Agent': 'SafeVixAIChatbot/1.0'},
            )

    @pytest.mark.asyncio
    async def test_lookup_open_meteo_succeeds(self):
        settings = _make_weather_settings()
        mock_om = AsyncMock(spec=OpenMeteoClient)
        mock_om.lookup.return_value = {
            "source": "open-meteo",
            "temperature": 25.0,
            "summary": "Clear sky",
        }
        with patch('tools.weather_tool.OpenMeteoClient', return_value=mock_om), \
             patch('tools.weather_tool.httpx.AsyncClient'):
            tool = WeatherTool(settings)
            result = await tool.lookup(lat=13.0, lon=80.0)

            assert result == {
                "source": "open-meteo",
                "temperature": 25.0,
                "summary": "Clear sky",
            }
            mock_om.lookup.assert_awaited_once_with(lat=13.0, lon=80.0)

    @pytest.mark.asyncio
    async def test_lookup_open_meteo_fails_owm_succeeds(self):
        settings = _make_weather_settings()
        mock_om = AsyncMock(spec=OpenMeteoClient)
        mock_om.lookup.return_value = None

        mock_http = AsyncMock(spec=httpx.AsyncClient)
        owm_resp = MagicMock()
        owm_resp.json.return_value = {
            "weather": [{"description": "partly cloudy"}],
            "main": {"temp": 22.0},
        }
        mock_http.get = AsyncMock(return_value=owm_resp)

        with patch('tools.weather_tool.OpenMeteoClient', return_value=mock_om), \
             patch('tools.weather_tool.httpx.AsyncClient', return_value=mock_http):
            tool = WeatherTool(settings)
            result = await tool.lookup(lat=12.97, lon=77.59)

            assert result == {
                "summary": "partly cloudy",
                "temperature": 22.0,
                "source": "openweathermap",
            }
            mock_om.lookup.assert_awaited_once_with(lat=12.97, lon=77.59)
            mock_http.get.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_lookup_both_fail_returns_none(self):
        settings = _make_weather_settings()
        mock_om = AsyncMock(spec=OpenMeteoClient)
        mock_om.lookup.return_value = None
        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_http.get = AsyncMock(side_effect=httpx.HTTPStatusError(
            "error", request=MagicMock(), response=MagicMock(),
        ))

        with patch('tools.weather_tool.OpenMeteoClient', return_value=mock_om), \
             patch('tools.weather_tool.httpx.AsyncClient', return_value=mock_http):
            tool = WeatherTool(settings)
            result = await tool.lookup(lat=0.0, lon=0.0)

            assert result is None

    @pytest.mark.asyncio
    async def test_owm_lookup_no_api_key_returns_none(self):
        settings = _make_weather_settings(openweather_api_key=None)
        with patch('tools.weather_tool.OpenMeteoClient'), \
             patch('tools.weather_tool.httpx.AsyncClient'):
            tool = WeatherTool(settings)
            result = await tool._owm_lookup(lat=13.0, lon=80.0)
            assert result is None

    @pytest.mark.asyncio
    async def test_owm_lookup_success_parses_weather_main(self):
        settings = _make_weather_settings()
        mock_http = AsyncMock(spec=httpx.AsyncClient)
        owm_resp = MagicMock()
        owm_resp.json.return_value = {
            "weather": [{"description": "clear sky"}],
            "main": {"temp": 30.5},
        }
        mock_http.get = AsyncMock(return_value=owm_resp)

        with patch('tools.weather_tool.OpenMeteoClient'), \
             patch('tools.weather_tool.httpx.AsyncClient', return_value=mock_http):
            tool = WeatherTool(settings)
            result = await tool._owm_lookup(lat=13.0, lon=80.0)

            assert result == {
                "summary": "clear sky",
                "temperature": 30.5,
                "source": "openweathermap",
            }

    @pytest.mark.asyncio
    async def test_owm_lookup_http_error_returns_none(self):
        settings = _make_weather_settings()
        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_http.get = AsyncMock(side_effect=httpx.HTTPStatusError(
            "error", request=MagicMock(), response=MagicMock(),
        ))

        with patch('tools.weather_tool.OpenMeteoClient'), \
             patch('tools.weather_tool.httpx.AsyncClient', return_value=mock_http):
            tool = WeatherTool(settings)
            result = await tool._owm_lookup(lat=0.0, lon=0.0)
            assert result is None

    @pytest.mark.asyncio
    async def test_aclose_closes_both_clients(self):
        mock_om = AsyncMock(spec=OpenMeteoClient)
        mock_http = AsyncMock(spec=httpx.AsyncClient)

        with patch('tools.weather_tool.OpenMeteoClient', return_value=mock_om), \
             patch('tools.weather_tool.httpx.AsyncClient', return_value=mock_http):
            tool = WeatherTool(_make_weather_settings())
            await tool.aclose()
            mock_om.aclose.assert_awaited_once()
            mock_http.aclose.assert_awaited_once()


# ===================================================================
# GeocodingClient
# ===================================================================

class TestGeocodingClient:

    def test_constructor_stores_opencage_key_and_creates_client(self):
        with patch('tools.geocoding.httpx.AsyncClient') as mock_cls:
            client = GeocodingClient(opencage_key="my-key", timeout=15.0, user_agent="test/1.0")
            assert client.opencage_key == "my-key"
            mock_cls.assert_called_once_with(
                timeout=15.0,
                headers={"User-Agent": "test/1.0"},
            )

    @pytest.mark.asyncio
    async def test_reverse_geocode_nominatim_succeeds(self):
        client = GeocodingClient(opencage_key=None)
        nom_resp = MagicMock()
        nom_resp.json.return_value = {
            "address": {
                "road": "Anna Salai",
                "city": "Chennai",
                "state": "Tamil Nadu",
                "postcode": "600002",
            },
            "display_name": "Anna Salai, Chennai, Tamil Nadu, India",
        }

        with patch.object(client._client, "get", AsyncMock(return_value=nom_resp)):
            result = await client.reverse_geocode(lat=13.0, lon=80.0)

            assert result == {
                "road": "Anna Salai",
                "city": "Chennai",
                "state": "Tamil Nadu",
                "postcode": "600002",
                "display": "Anna Salai, Chennai, Tamil Nadu",
                "source": "nominatim",
            }

    @pytest.mark.asyncio
    async def test_reverse_geocode_nominatim_fails_opencage_succeeds(self):
        client = GeocodingClient(opencage_key="valid-key")
        nom_resp = MagicMock()
        nom_resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            "error", request=MagicMock(), response=MagicMock(status_code=404),
        )
        oc_resp = MagicMock()
        oc_resp.json.return_value = {
            "results": [{
                "components": {
                    "road": "MG Road",
                    "city": "Bangalore",
                    "state": "Karnataka",
                    "postcode": "560001",
                },
                "formatted": "MG Road, Bangalore, Karnataka, India",
            }],
        }

        with patch.object(client._client, "get", AsyncMock(side_effect=[nom_resp, oc_resp])):
            result = await client.reverse_geocode(lat=12.97, lon=77.59)

            assert result["road"] == "MG Road"
            assert result["city"] == "Bangalore"
            assert result["source"] == "opencage"

    @pytest.mark.asyncio
    async def test_reverse_geocode_both_fail_returns_none(self):
        client = GeocodingClient(opencage_key="valid-key")
        nom_resp = MagicMock()
        nom_resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            "error", request=MagicMock(), response=MagicMock(status_code=404),
        )
        oc_resp = MagicMock()
        oc_resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            "error", request=MagicMock(), response=MagicMock(status_code=404),
        )

        with patch.object(client._client, "get", AsyncMock(side_effect=[nom_resp, oc_resp])):
            result = await client.reverse_geocode(lat=0.0, lon=0.0)
            assert result is None

    @pytest.mark.asyncio
    async def test_nominatim_reverse_success(self):
        client = GeocodingClient(opencage_key=None)
        nom_resp = MagicMock()
        nom_resp.json.return_value = {
            "address": {
                "road": "Marine Drive",
                "city": "Mumbai",
                "state": "Maharashtra",
                "postcode": "400001",
            },
            "display_name": "Marine Drive, Mumbai, Maharashtra, India",
        }

        with patch.object(client._client, "get", AsyncMock(return_value=nom_resp)):
            result = await client._nominatim_reverse(lat=19.0, lon=72.8)

            assert result == {
                "road": "Marine Drive",
                "city": "Mumbai",
                "state": "Maharashtra",
                "postcode": "400001",
                "display": "Marine Drive, Mumbai, Maharashtra",
                "source": "nominatim",
            }

    @pytest.mark.asyncio
    async def test_nominatim_reverse_http_error_returns_none(self):
        client = GeocodingClient(opencage_key=None)
        with patch.object(client._client, "get", AsyncMock(side_effect=httpx.HTTPStatusError(
            "error", request=MagicMock(), response=MagicMock(),
        ))):
            result = await client._nominatim_reverse(lat=0.0, lon=0.0)
            assert result is None

    @pytest.mark.asyncio
    async def test_nominatim_reverse_json_decode_error_returns_none(self):
        client = GeocodingClient(opencage_key=None)
        nom_resp = MagicMock()
        nom_resp.json.side_effect = json.JSONDecodeError("bad json", "", 0)

        with patch.object(client._client, "get", AsyncMock(return_value=nom_resp)):
            result = await client._nominatim_reverse(lat=0.0, lon=0.0)
            assert result is None

    @pytest.mark.asyncio
    async def test_nominatim_reverse_missing_address_fields_falls_back_gracefully(self):
        client = GeocodingClient(opencage_key=None)
        nom_resp = MagicMock()
        nom_resp.json.return_value = {
            "address": {"state": "Karnataka"},
            "display_name": "Somewhere, Karnataka, India",
        }

        with patch.object(client._client, "get", AsyncMock(return_value=nom_resp)):
            result = await client._nominatim_reverse(lat=12.97, lon=77.59)

            assert result["road"] == ""
            assert result["city"] == ""
            assert result["state"] == "Karnataka"
            assert result["postcode"] == ""
            assert result["display"] == "Karnataka"
            assert result["source"] == "nominatim"

    @pytest.mark.asyncio
    async def test_nominatim_reverse_empty_address_falls_back_to_display_name(self):
        client = GeocodingClient(opencage_key=None)
        nom_resp = MagicMock()
        nom_resp.json.return_value = {
            "display_name": "Unknown Location",
        }

        with patch.object(client._client, "get", AsyncMock(return_value=nom_resp)):
            result = await client._nominatim_reverse(lat=0.0, lon=0.0)

            assert result["road"] == ""
            assert result["city"] == ""
            assert result["display"] == "Unknown Location"
            assert result["source"] == "nominatim"

    @pytest.mark.asyncio
    async def test_opencage_reverse_no_key_returns_none(self):
        with patch.dict('os.environ', {'OPENCAGE_API_KEY': ''}, clear=False):
            client = GeocodingClient(opencage_key=None)
            result = await client._opencage_reverse(lat=13.0, lon=80.0)
            assert result is None

    @pytest.mark.asyncio
    async def test_opencage_reverse_success(self):
        client = GeocodingClient(opencage_key="valid-key")
        oc_resp = MagicMock()
        oc_resp.json.return_value = {
            "results": [{
                "components": {
                    "road": "Brigade Road",
                    "city": "Bangalore",
                    "state": "Karnataka",
                    "postcode": "560001",
                },
                "formatted": "Brigade Road, Bangalore, Karnataka, India",
            }],
        }

        with patch.object(client._client, "get", AsyncMock(return_value=oc_resp)):
            result = await client._opencage_reverse(lat=12.97, lon=77.59)

            assert result == {
                "road": "Brigade Road",
                "city": "Bangalore",
                "state": "Karnataka",
                "postcode": "560001",
                "display": "Brigade Road, Bangalore, Karnataka, India",
                "source": "opencage",
            }

    @pytest.mark.asyncio
    async def test_opencage_reverse_no_results_returns_none(self):
        client = GeocodingClient(opencage_key="valid-key")
        oc_resp = MagicMock()
        oc_resp.json.return_value = {"results": []}

        with patch.object(client._client, "get", AsyncMock(return_value=oc_resp)):
            result = await client._opencage_reverse(lat=0.0, lon=0.0)
            assert result is None

    @pytest.mark.asyncio
    async def test_opencage_reverse_http_error_returns_none(self):
        client = GeocodingClient(opencage_key="valid-key")
        with patch.object(client._client, "get", AsyncMock(side_effect=httpx.HTTPStatusError(
            "error", request=MagicMock(), response=MagicMock(),
        ))):
            result = await client._opencage_reverse(lat=0.0, lon=0.0)
            assert result is None

    @pytest.mark.asyncio
    async def test_aclose_closes_underlying_client(self):
        client = GeocodingClient(opencage_key=None)
        with patch.object(client._client, "aclose", AsyncMock()) as mock_aclose:
            await client.aclose()
            mock_aclose.assert_awaited_once()
