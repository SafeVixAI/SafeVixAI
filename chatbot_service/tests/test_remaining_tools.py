# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from config import Settings
from tools.drug_info import DrugInfoTool, _extract_first
from tools.open_meteo import OpenMeteoClient
from tools.submit_report_tool import SubmitReportTool
from tools.what3words import What3WordsTool

_SETTINGS = Settings(
    environment='test',
    service_name='test',
    service_port=0,
    cors_origins='',
    main_backend_base_url='',
    main_backend_timeout_seconds=5.0,
    redis_url=None,
    internal_api_key=None,
    chroma_persist_dir=Path('.'),
    rag_data_dir=Path('.'),
    embedding_model='test',
    rag_min_score=0.0,
    top_k_retrieval=1,
    default_llm_provider='test',
    default_llm_model='test',
    speech_model_id='test',
    speech_model_dir=None,
    speech_device='cpu',
    speech_default_target_lang='eng',
    openweather_api_key=None,
    openweather_base_url='',
    openweather_units='metric',
    w3w_api_key=None,
    opencage_api_key=None,
    http_timeout_seconds=20.0,
    http_user_agent='SafeVixAIChatbot/1.0',
    session_ttl_seconds=3600,
    admin_secret=None,
    sentry_dsn=None,
)


# =============================================================================
# OpenMeteoClient Tests
# =============================================================================

@pytest.mark.asyncio
async def test_openmeteo_constructor_creates_httpx_client():
    with patch('tools.open_meteo.httpx.AsyncClient') as mock_cls:
        mock_instance = MagicMock()
        mock_cls.return_value = mock_instance
        tool = OpenMeteoClient(_SETTINGS)
    mock_cls.assert_called_once_with(
        timeout=20.0,
        headers={"User-Agent": "SafeVixAIChatbot/1.0"},
    )
    assert tool._client is mock_instance


@pytest.mark.asyncio
async def test_openmeteo_lookup_clear_weather():
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "current_weather": {"weathercode": 0, "temperature": 25.0, "windspeed": 10.0},
        "hourly": {"precipitation_probability": [5], "visibility": [10000]},
    }
    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=mock_response)

    with patch('tools.open_meteo.httpx.AsyncClient', return_value=mock_client):
        tool = OpenMeteoClient(_SETTINGS)
        result = await tool.lookup(lat=13.0, lon=80.0)

    assert result is not None
    assert result["summary"] == "Clear sky"
    assert result["temperature"] == 25.0
    assert result["wind_speed_kmh"] == 10.0
    assert result["risk_multiplier"] == 1.0
    assert result["precipitation_probability"] == 5
    assert result["visibility_meters"] == 10000
    assert result["weather_code"] == 0
    assert result["source"] == "open-meteo"

    call_kwargs = mock_client.get.call_args.kwargs
    assert call_kwargs["params"]["latitude"] == 13.0
    assert call_kwargs["params"]["longitude"] == 80.0
    assert call_kwargs["params"]["current_weather"] == "true"


@pytest.mark.asyncio
async def test_openmeteo_lookup_thunderstorm_risk():
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "current_weather": {"weathercode": 95, "temperature": 20.0, "windspeed": 30.0},
        "hourly": {"precipitation_probability": [80], "visibility": [5000]},
    }
    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=mock_response)

    with patch('tools.open_meteo.httpx.AsyncClient', return_value=mock_client):
        tool = OpenMeteoClient(_SETTINGS)
        result = await tool.lookup(lat=13.0, lon=80.0)

    assert result is not None
    assert result["risk_multiplier"] == 2.2
    assert result["summary"] == "Thunderstorm"


@pytest.mark.asyncio
async def test_openmeteo_lookup_fog_risk():
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "current_weather": {"weathercode": 45, "temperature": 15.0, "windspeed": 5.0},
        "hourly": {"precipitation_probability": [20], "visibility": [6000]},
    }
    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=mock_response)

    with patch('tools.open_meteo.httpx.AsyncClient', return_value=mock_client):
        tool = OpenMeteoClient(_SETTINGS)
        result = await tool.lookup(lat=13.0, lon=80.0)

    assert result is not None
    assert result["risk_multiplier"] == 1.8
    assert result["summary"] == "Fog"


@pytest.mark.asyncio
async def test_openmeteo_lookup_low_visibility_bumps_risk():
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "current_weather": {"weathercode": 0, "temperature": 25.0, "windspeed": 5.0},
        "hourly": {"precipitation_probability": [0], "visibility": [500]},
    }
    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=mock_response)

    with patch('tools.open_meteo.httpx.AsyncClient', return_value=mock_client):
        tool = OpenMeteoClient(_SETTINGS)
        result = await tool.lookup(lat=13.0, lon=80.0)

    assert result is not None
    assert result["risk_multiplier"] == 2.0
    assert result["visibility_meters"] == 500


@pytest.mark.asyncio
async def test_openmeteo_lookup_moderate_visibility_bumps_risk():
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "current_weather": {"weathercode": 0, "temperature": 25.0, "windspeed": 5.0},
        "hourly": {"precipitation_probability": [0], "visibility": [3000]},
    }
    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=mock_response)

    with patch('tools.open_meteo.httpx.AsyncClient', return_value=mock_client):
        tool = OpenMeteoClient(_SETTINGS)
        result = await tool.lookup(lat=13.0, lon=80.0)

    assert result is not None
    assert result["risk_multiplier"] == 1.5
    assert result["visibility_meters"] == 3000


@pytest.mark.asyncio
async def test_openmeteo_lookup_high_visibility_no_risk_bump():
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "current_weather": {"weathercode": 0, "temperature": 25.0, "windspeed": 5.0},
        "hourly": {"precipitation_probability": [0], "visibility": [8000]},
    }
    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=mock_response)

    with patch('tools.open_meteo.httpx.AsyncClient', return_value=mock_client):
        tool = OpenMeteoClient(_SETTINGS)
        result = await tool.lookup(lat=13.0, lon=80.0)

    assert result is not None
    assert result["risk_multiplier"] == 1.0


@pytest.mark.asyncio
async def test_openmeteo_lookup_missing_current_weather():
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {}
    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=mock_response)

    with patch('tools.open_meteo.httpx.AsyncClient', return_value=mock_client):
        tool = OpenMeteoClient(_SETTINGS)
        result = await tool.lookup(lat=13.0, lon=80.0)

    assert result is not None
    assert result["summary"] == "Clear sky"
    assert result["temperature"] is None
    assert result["wind_speed_kmh"] is None
    assert result["risk_multiplier"] == 1.0


@pytest.mark.asyncio
async def test_openmeteo_lookup_missing_hourly_data():
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "current_weather": {"weathercode": 0, "temperature": 25.0, "windspeed": 10.0},
    }
    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=mock_response)

    with patch('tools.open_meteo.httpx.AsyncClient', return_value=mock_client):
        tool = OpenMeteoClient(_SETTINGS)
        result = await tool.lookup(lat=13.0, lon=80.0)

    assert result is not None
    assert result["precipitation_probability"] is None
    assert result["visibility_meters"] is None


@pytest.mark.asyncio
async def test_openmeteo_lookup_http_error_returns_none():
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "500 error", request=MagicMock(), response=MagicMock(status_code=500)
    )
    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=mock_response)

    with patch('tools.open_meteo.httpx.AsyncClient', return_value=mock_client):
        tool = OpenMeteoClient(_SETTINGS)
        result = await tool.lookup(lat=13.0, lon=80.0)

    assert result is None


@pytest.mark.asyncio
async def test_openmeteo_lookup_timeout_returns_none():
    mock_client = MagicMock()
    mock_client.get = AsyncMock(side_effect=httpx.TimeoutException("timeout", request=MagicMock()))

    with patch('tools.open_meteo.httpx.AsyncClient', return_value=mock_client):
        tool = OpenMeteoClient(_SETTINGS)
        result = await tool.lookup(lat=13.0, lon=80.0)

    assert result is None


@pytest.mark.asyncio
async def test_openmeteo_lookup_json_decode_error_returns_none():
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.side_effect = json.JSONDecodeError("bad json", "doc", 0)
    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=mock_response)

    with patch('tools.open_meteo.httpx.AsyncClient', return_value=mock_client):
        tool = OpenMeteoClient(_SETTINGS)
        result = await tool.lookup(lat=13.0, lon=80.0)

    assert result is None


@pytest.mark.asyncio
async def test_openmeteo_lookup_unknown_weather_code():
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "current_weather": {"weathercode": 999, "temperature": 20.0, "windspeed": 5.0},
        "hourly": {"precipitation_probability": [0], "visibility": [10000]},
    }
    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=mock_response)

    with patch('tools.open_meteo.httpx.AsyncClient', return_value=mock_client):
        tool = OpenMeteoClient(_SETTINGS)
        result = await tool.lookup(lat=13.0, lon=80.0)

    assert result is not None
    assert result["summary"] == "Unknown"
    assert result["risk_multiplier"] == 1.0


@pytest.mark.asyncio
async def test_openmeteo_lookup_precipitation_included():
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "current_weather": {"weathercode": 61, "temperature": 18.0, "windspeed": 12.0},
        "hourly": {"precipitation_probability": [75], "visibility": [4000]},
    }
    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=mock_response)

    with patch('tools.open_meteo.httpx.AsyncClient', return_value=mock_client):
        tool = OpenMeteoClient(_SETTINGS)
        result = await tool.lookup(lat=13.0, lon=80.0)

    assert result is not None
    assert result["precipitation_probability"] == 75
    assert result["weather_code"] == 61
    assert result["summary"] == "Slight rain"


@pytest.mark.asyncio
async def test_openmeteo_lookup_wind_and_temperature():
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "current_weather": {"weathercode": 0, "temperature": 32.5, "windspeed": 15.3},
        "hourly": {"precipitation_probability": [10], "visibility": [12000]},
    }
    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=mock_response)

    with patch('tools.open_meteo.httpx.AsyncClient', return_value=mock_client):
        tool = OpenMeteoClient(_SETTINGS)
        result = await tool.lookup(lat=13.0, lon=80.0)

    assert result is not None
    assert result["temperature"] == 32.5
    assert result["wind_speed_kmh"] == 15.3


@pytest.mark.asyncio
async def test_openmeteo_aclose_closes_client():
    mock_client = MagicMock()
    mock_client.aclose = AsyncMock()

    with patch('tools.open_meteo.httpx.AsyncClient', return_value=mock_client):
        tool = OpenMeteoClient(_SETTINGS)
        await tool.aclose()

    mock_client.aclose.assert_awaited_once()


# =============================================================================
# What3WordsTool Tests
# =============================================================================

@pytest.mark.asyncio
async def test_w3w_constructor_stores_api_key():
    tool = What3WordsTool(api_key="test-key-123")
    assert tool.api_key == "test-key-123"
    assert tool._client is not None


@pytest.mark.asyncio
async def test_w3w_gps_to_words_no_api_key():
    with patch('tools.what3words.os.getenv', return_value=""):
        tool = What3WordsTool(api_key=None)
    result = await tool.gps_to_words(lat=13.0, lon=80.0)
    assert result is None


@pytest.mark.asyncio
async def test_w3w_gps_to_words_success():
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {"words": "filled.count.soap"}
    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=mock_response)

    with patch('tools.what3words.httpx.AsyncClient', return_value=mock_client):
        tool = What3WordsTool(api_key="test-key")
        result = await tool.gps_to_words(lat=51.521, lon=-0.129)

    assert result is not None
    assert result["words"] == "filled.count.soap"
    assert result["map_url"] == "https://w3w.co/filled.count.soap"
    assert result["formatted"] == "///filled.count.soap"

    call_kwargs = mock_client.get.call_args.kwargs
    assert call_kwargs["params"]["coordinates"] == "51.521,-0.129"
    assert call_kwargs["params"]["key"] == "test-key"


@pytest.mark.asyncio
async def test_w3w_gps_to_words_empty_words_returns_none():
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {"words": ""}
    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=mock_response)

    with patch('tools.what3words.httpx.AsyncClient', return_value=mock_client):
        tool = What3WordsTool(api_key="test-key")
        result = await tool.gps_to_words(lat=13.0, lon=80.0)

    assert result is None


@pytest.mark.asyncio
async def test_w3w_gps_to_words_http_error_returns_none():
    mock_client = MagicMock()
    mock_client.get = AsyncMock(side_effect=httpx.HTTPStatusError(
        "403", request=MagicMock(), response=MagicMock(status_code=403)
    ))

    with patch('tools.what3words.httpx.AsyncClient', return_value=mock_client):
        tool = What3WordsTool(api_key="test-key")
        result = await tool.gps_to_words(lat=13.0, lon=80.0)

    assert result is None


@pytest.mark.asyncio
async def test_w3w_gps_to_words_json_error_returns_none():
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.side_effect = json.JSONDecodeError("bad", "doc", 0)
    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=mock_response)

    with patch('tools.what3words.httpx.AsyncClient', return_value=mock_client):
        tool = What3WordsTool(api_key="test-key")
        result = await tool.gps_to_words(lat=13.0, lon=80.0)

    assert result is None


@pytest.mark.asyncio
async def test_w3w_words_to_gps_no_api_key():
    with patch('tools.what3words.os.getenv', return_value=""):
        tool = What3WordsTool(api_key=None)
    result = await tool.words_to_gps("filled.count.soap")
    assert result is None


@pytest.mark.asyncio
async def test_w3w_words_to_gps_success():
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "coordinates": {"lat": 51.521, "lng": -0.129}
    }
    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=mock_response)

    with patch('tools.what3words.httpx.AsyncClient', return_value=mock_client):
        tool = What3WordsTool(api_key="test-key")
        result = await tool.words_to_gps("filled.count.soap")

    assert result is not None
    assert result["lat"] == 51.521
    assert result["lon"] == -0.129


@pytest.mark.asyncio
async def test_w3w_words_to_gps_http_error_returns_none():
    mock_client = MagicMock()
    mock_client.get = AsyncMock(side_effect=httpx.HTTPStatusError(
        "404", request=MagicMock(), response=MagicMock(status_code=404)
    ))

    with patch('tools.what3words.httpx.AsyncClient', return_value=mock_client):
        tool = What3WordsTool(api_key="test-key")
        result = await tool.words_to_gps("filled.count.soap")

    assert result is None


@pytest.mark.asyncio
async def test_w3w_words_to_gps_strips_prefix():
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "coordinates": {"lat": 51.521, "lng": -0.129}
    }
    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=mock_response)

    with patch('tools.what3words.httpx.AsyncClient', return_value=mock_client):
        tool = What3WordsTool(api_key="test-key")
        result = await tool.words_to_gps("///filled.count.soap")

    assert result is not None
    call_params = mock_client.get.call_args.kwargs["params"]
    assert call_params["words"] == "filled.count.soap"


@pytest.mark.asyncio
async def test_w3w_aclose_closes_client():
    mock_client = MagicMock()
    mock_client.aclose = AsyncMock()

    with patch('tools.what3words.httpx.AsyncClient', return_value=mock_client):
        tool = What3WordsTool(api_key="test-key")
        await tool.aclose()

    mock_client.aclose.assert_awaited_once()


# =============================================================================
# DrugInfoTool Tests
# =============================================================================

@pytest.mark.asyncio
async def test_druginfo_constructor_creates_httpx_client():
    with patch('tools.drug_info.httpx.AsyncClient') as mock_cls:
        tool = DrugInfoTool(timeout=10.0)
    mock_cls.assert_called_once_with(timeout=10.0)
    assert tool._client is not None


@pytest.mark.asyncio
async def test_druginfo_lookup_empty_name_returns_none():
    tool = DrugInfoTool()
    with patch.object(tool, '_client'):
        result = await tool.lookup("")
    assert result is None


@pytest.mark.asyncio
async def test_druginfo_lookup_whitespace_only_returns_none():
    tool = DrugInfoTool()
    with patch.object(tool, '_client'):
        result = await tool.lookup("   ")
    assert result is None


@pytest.mark.asyncio
async def test_druginfo_lookup_success():
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "results": [{
            "indications_and_usage": ["For relief of pain and fever"],
            "warnings": ["Do not exceed recommended dose"],
            "dosage_and_administration": ["Take 1 tablet every 6 hours"],
            "contraindications": ["Liver disease"],
            "active_ingredient": ["Paracetamol 500mg"],
        }]
    }
    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=mock_response)

    with patch('tools.drug_info.httpx.AsyncClient', return_value=mock_client):
        tool = DrugInfoTool()
        result = await tool.lookup("paracetamol")

    assert result is not None
    assert result["drug_name"] == "paracetamol"
    assert result["indications"] == "For relief of pain and fever"
    assert result["warnings"] == "Do not exceed recommended dose"
    assert result["dosage"] == "Take 1 tablet every 6 hours"
    assert result["contraindications"] == "Liver disease"
    assert result["active_ingredient"] == "Paracetamol 500mg"
    assert result["source"] == "openfda"

    call_kwargs = mock_client.get.call_args.kwargs
    assert call_kwargs["params"]["search"] == "paracetamol"
    assert call_kwargs["params"]["limit"] == 1


@pytest.mark.asyncio
async def test_druginfo_lookup_no_results_returns_none():
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {"results": []}
    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=mock_response)

    with patch('tools.drug_info.httpx.AsyncClient', return_value=mock_client):
        tool = DrugInfoTool()
        result = await tool.lookup("nonexistentdrugxyz")
    assert result is None


@pytest.mark.asyncio
async def test_druginfo_lookup_truncates_long_text():
    long_text = "x" * 1500
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "results": [{
            "indications_and_usage": [long_text],
            "warnings": ["Short warning"],
        }]
    }
    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=mock_response)

    with patch('tools.drug_info.httpx.AsyncClient', return_value=mock_client):
        tool = DrugInfoTool()
        result = await tool.lookup("drug")

    assert result is not None
    assert len(result["indications"]) == 1003
    assert result["indications"].endswith("...")
    assert result["warnings"] == "Short warning"


@pytest.mark.asyncio
async def test_druginfo_lookup_http_error_returns_none():
    mock_client = MagicMock()
    mock_client.get = AsyncMock(side_effect=httpx.HTTPStatusError(
        "500", request=MagicMock(), response=MagicMock(status_code=500)
    ))

    with patch('tools.drug_info.httpx.AsyncClient', return_value=mock_client):
        tool = DrugInfoTool()
        result = await tool.lookup("paracetamol")
    assert result is None


@pytest.mark.asyncio
async def test_druginfo_lookup_json_error_returns_none():
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.side_effect = json.JSONDecodeError("bad", "doc", 0)
    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=mock_response)

    with patch('tools.drug_info.httpx.AsyncClient', return_value=mock_client):
        tool = DrugInfoTool()
        result = await tool.lookup("paracetamol")
    assert result is None


def test_druginfo_extract_first_key_exists():
    label = {"indications_and_usage": ["Take with food"]}
    assert _extract_first(label, "indications_and_usage") == "Take with food"


def test_druginfo_extract_first_key_missing():
    label = {"other": ["value"]}
    assert _extract_first(label, "nonexistent") == ""


def test_druginfo_extract_first_empty_list():
    label = {"indications_and_usage": []}
    assert _extract_first(label, "indications_and_usage") == ""


# =============================================================================
# SubmitReportTool Tests
# =============================================================================

def test_submitreport_constructor_lazy_client():
    tool = SubmitReportTool(backend_base_url="http://localhost:8000")
    assert tool._base_url == "http://localhost:8000"
    assert tool._client is None


@pytest.mark.asyncio
async def test_submitreport_no_base_url_returns_guidance():
    tool = SubmitReportTool(backend_base_url=None)
    result = await tool.submit(issue_type="pothole")
    assert result["submitted"] is False
    assert "pothole" in result["summary"]
    assert result["issue_type"] == "pothole"


@pytest.mark.asyncio
async def test_submitreport_success():
    tool = SubmitReportTool(backend_base_url="http://localhost:8000")
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {"uuid": "abc-123", "complaint_ref": "REF001"}
    mock_client = MagicMock()
    mock_client.post = AsyncMock(return_value=mock_response)

    with patch.object(tool, '_get_client', return_value=mock_client):
        result = await tool.submit(issue_type="pothole", severity="medium")

    assert result["submitted"] is True
    assert result["report_id"] == "abc-123"
    assert result["complaint_ref"] == "REF001"
    assert result["issue_type"] == "pothole"
    assert "REF001" in result["message"]

    call_kwargs = mock_client.post.call_args.kwargs
    assert call_kwargs["json"]["issue_type"] == "pothole"
    assert call_kwargs["json"]["severity"] == "2"


@pytest.mark.asyncio
async def test_submitreport_severity_string_normalized():
    tool = SubmitReportTool(backend_base_url="http://localhost:8000")
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {"uuid": "abc-123"}
    mock_client = MagicMock()
    mock_client.post = AsyncMock(return_value=mock_response)

    with patch.object(tool, '_get_client', return_value=mock_client):
        await tool.submit(issue_type="pothole", severity="high")

    call_kwargs = mock_client.post.call_args.kwargs
    assert call_kwargs["json"]["severity"] == "4"


@pytest.mark.asyncio
async def test_submitreport_severity_int_clamped():
    tool = SubmitReportTool(backend_base_url="http://localhost:8000")
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {"uuid": "abc-123"}
    mock_client = MagicMock()
    mock_client.post = AsyncMock(return_value=mock_response)

    with patch.object(tool, '_get_client', return_value=mock_client):
        await tool.submit(issue_type="pothole", severity=10)

    call_kwargs = mock_client.post.call_args.kwargs
    assert call_kwargs["json"]["severity"] == "5"


@pytest.mark.asyncio
async def test_submitreport_http_error_returns_guidance():
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "500", request=MagicMock(), response=MagicMock(status_code=500)
    )
    mock_client = MagicMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    tool = SubmitReportTool(backend_base_url="http://localhost:8000")

    with patch.object(tool, '_get_client', return_value=mock_client):
        result = await tool.submit(issue_type="pothole")

    assert result["submitted"] is False
    assert "error" in result["summary"].lower() or "Backend returned an error" in result["summary"]


@pytest.mark.asyncio
async def test_submitreport_general_exception_returns_guidance():
    mock_client = MagicMock()
    mock_client.post = AsyncMock(side_effect=RuntimeError("connection failed"))
    tool = SubmitReportTool(backend_base_url="http://localhost:8000")

    with patch.object(tool, '_get_client', return_value=mock_client):
        result = await tool.submit(issue_type="pothole")

    assert result["submitted"] is False


@pytest.mark.asyncio
async def test_submitreport_with_lat_lon_includes_coords():
    tool = SubmitReportTool(backend_base_url="http://localhost:8000")
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {"uuid": "abc-123"}
    mock_client = MagicMock()
    mock_client.post = AsyncMock(return_value=mock_response)

    with patch.object(tool, '_get_client', return_value=mock_client):
        await tool.submit(issue_type="pothole", lat=13.0827, lon=80.2707)

    call_kwargs = mock_client.post.call_args.kwargs
    assert call_kwargs["json"]["lat"] == 13.0827
    assert call_kwargs["json"]["lon"] == 80.2707


@pytest.mark.asyncio
async def test_submitreport_without_lat_lon_no_coords():
    tool = SubmitReportTool(backend_base_url="http://localhost:8000")
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {"uuid": "abc-123"}
    mock_client = MagicMock()
    mock_client.post = AsyncMock(return_value=mock_response)

    with patch.object(tool, '_get_client', return_value=mock_client):
        await tool.submit(issue_type="pothole")

    call_kwargs = mock_client.post.call_args.kwargs
    assert "lat" not in call_kwargs["json"]
    assert "lon" not in call_kwargs["json"]


@pytest.mark.asyncio
async def test_submitreport_long_description_truncated():
    tool = SubmitReportTool(backend_base_url="http://localhost:8000")
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {"uuid": "abc-123"}
    mock_client = MagicMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    long_desc = "x" * 70000

    with patch.object(tool, '_get_client', return_value=mock_client):
        await tool.submit(issue_type="pothole", description=long_desc)

    call_kwargs = mock_client.post.call_args.kwargs
    assert len(call_kwargs["json"]["description"]) == 65536


def test_submitreport_normalize_severity_strings():
    assert SubmitReportTool._normalize_severity("low") == 1
    assert SubmitReportTool._normalize_severity("minor") == 1
    assert SubmitReportTool._normalize_severity("medium") == 2
    assert SubmitReportTool._normalize_severity("moderate") == 2
    assert SubmitReportTool._normalize_severity("high") == 4
    assert SubmitReportTool._normalize_severity("critical") == 5
    assert SubmitReportTool._normalize_severity("severe") == 5


def test_submitreport_normalize_severity_unrecognized_defaults_to_2():
    assert SubmitReportTool._normalize_severity("unknown") == 2
    assert SubmitReportTool._normalize_severity("") == 2


def test_submitreport_normalize_severity_digit_string():
    assert SubmitReportTool._normalize_severity("5") == 5
    assert SubmitReportTool._normalize_severity("3") == 3
