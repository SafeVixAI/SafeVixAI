# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team
"""Service layer coverage: llm_service, safe_routing, safe_spaces.

Targets branches NOT already exercised in:
  - tests/test_llm_service.py
  - tests/test_safe_routing.py
  - tests/test_safe_spaces.py
"""

from __future__ import annotations

import asyncio
import json
import uuid
from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

import httpx
import pytest

import services.safe_spaces as _ss_module
from core.config import Settings
from models.schemas import ChatRequest, ChatResponse
from services.exceptions import ExternalServiceError, ServiceValidationError
from services.llm_service import LLMService
from services.safe_routing import _osrm_fallback, _validate_coords, get_safe_route, is_nighttime
from services.safe_spaces import close_safe_spaces_client, get_safe_spaces

# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------


class _MockResponse:
    """Minimal httpx.Response substitute for safe_spaces testing."""

    def __init__(self, status_code: int, json_data: dict | None = None):
        self.status_code = status_code
        self._json_data = json_data if json_data is not None else {}

    def json(self):
        return self._json_data


_SAMPLE_ELEMENTS = [
    {
        "type": "node",
        "id": 1,
        "lat": 13.05,
        "lon": 80.25,
        "tags": {
            "name": "City Hospital",
            "amenity": "hospital",
            "phone": "044-12345678",
            "opening_hours": "24/7",
        },
    },
    {
        "type": "node",
        "id": 2,
        "lat": 13.06,
        "lon": 80.26,
        "tags": {"name": "Police HQ", "amenity": "police"},
    },
]

_OSRM_RESPONSE = {
    "routes": [
        {
            "distance": 4500.0,
            "duration": 270.0,
            "geometry": {"type": "LineString", "coordinates": [[77.59, 12.97]]},
        }
    ]
}

_ORS_RESPONSE = {
    "routes": [
        {
            "summary": {"distance": 5200.0, "duration": 310.0},
            "geometry": {"type": "LineString", "coordinates": [[77.59, 12.97]]},
        }
    ]
}


# ---------------------------------------------------------------------------
# Module-level fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def settings():
    s = MagicMock(spec=Settings)
    s.chatbot_service_url = "http://localhost:8010/api/v1"
    s.chatbot_request_timeout_seconds = 20.0
    s.http_user_agent = "SafeVixAI-Test/1.0"
    s.chatbot_internal_api_key = None
    return s


@pytest.fixture(autouse=True)
def _patch_json_on_llm_module():
    """services.llm_service references json.JSONDecodeError without an import statement.
    Provide it as a synthetic module attribute so the except clause evaluates cleanly."""
    with patch("services.llm_service.json", create=True) as mock_json:
        mock_json.JSONDecodeError = json.JSONDecodeError
        yield


@pytest.fixture(autouse=True)
async def _reset_safe_spaces_client():
    """Guarantee a clean global _CLIENT between tests."""
    yield
    await close_safe_spaces_client()


# ============================================================================
# LLM SERVICE — __init__ header count
# ============================================================================


class TestLLMServiceInitHeaders:
    """Verify exact header dict contents, not just presence/absence of a single key."""

    def test_no_api_key_produces_exactly_two_headers(self, settings):
        """Without a key, only Accept and User-Agent end up in the header dict."""
        with patch("services.llm_service.httpx.AsyncClient") as mock_cls:
            LLMService(settings)
        _, kwargs = mock_cls.call_args
        assert len(kwargs["headers"]) == 2
        assert "Accept" in kwargs["headers"]
        assert "User-Agent" in kwargs["headers"]

    def test_with_truthy_api_key_produces_exactly_three_headers(self, settings):
        """A non-empty api_key adds X-Internal-Api-Key as the third header."""
        settings.chatbot_internal_api_key = "sk-internal-secret"
        with patch("services.llm_service.httpx.AsyncClient") as mock_cls:
            LLMService(settings)
        _, kwargs = mock_cls.call_args
        assert len(kwargs["headers"]) == 3
        assert kwargs["headers"]["X-Internal-Api-Key"] == "sk-internal-secret"

    def test_empty_string_api_key_is_falsy_so_header_is_omitted(self, settings):
        """Empty string evaluates as falsy — X-Internal-Api-Key must be absent."""
        settings.chatbot_internal_api_key = ""
        with patch("services.llm_service.httpx.AsyncClient") as mock_cls:
            LLMService(settings)
        _, kwargs = mock_cls.call_args
        assert "X-Internal-Api-Key" not in kwargs["headers"]
        assert len(kwargs["headers"]) == 2


# ============================================================================
# LLM SERVICE — send_message edge cases
# ============================================================================


class TestLLMServiceSendMessageEdges:
    @pytest.fixture
    def service(self, settings):
        with patch("services.llm_service.httpx.AsyncClient", return_value=MagicMock()):
            return LLMService(settings)

    async def test_success_with_provided_session_id_returns_server_session(self, service):
        """In the success path session_id in ChatResponse comes from the JSON body,
        not from the request (the request session_id is only used for logging)."""
        mock_resp = MagicMock(spec=httpx.Response)
        mock_resp.json.return_value = {
            "response": "All good",
            "intent": "general",
            "sources": [],
            "session_id": "server-generated-id",
        }
        service._client.post = AsyncMock(return_value=mock_resp)

        result = await service.send_message(
            ChatRequest(message="status check", session_id="client-supplied-id")
        )

        assert isinstance(result, ChatResponse)
        assert result.session_id == "server-generated-id"
        assert result.intent == "general"

    async def test_builtin_timeout_error_returns_fallback(self, service):
        """Built-in TimeoutError (separate from asyncio.TimeoutError in Python ≤3.10)
        is also caught by the except (asyncio.TimeoutError, TimeoutError) clause."""
        service._client.post = AsyncMock(side_effect=TimeoutError("connection timed out"))
        result = await service.send_message(ChatRequest(message="ping"))
        assert result.intent == "fallback"
        assert result.session_id is not None

    async def test_builtin_timeout_preserves_explicit_session_id(self, service):
        """session_id from the request is preserved in the fallback on TimeoutError."""
        service._client.post = AsyncMock(side_effect=TimeoutError("timed out"))
        result = await service.send_message(ChatRequest(message="hello", session_id="pre-set-sess"))
        assert result.session_id == "pre-set-sess"

    async def test_connect_error_returns_fallback(self, service):
        """httpx.ConnectError is a RequestError subclass — caught by the RequestError handler."""
        service._client.post = AsyncMock(side_effect=httpx.ConnectError("connection refused"))
        result = await service.send_message(ChatRequest(message="probe"))
        assert result.intent == "fallback"

    async def test_auto_generated_session_id_is_valid_uuid4(self, service):
        """When no session_id is provided, the fallback generates a UUID4."""
        service._client.post = AsyncMock(side_effect=TimeoutError())
        result = await service.send_message(ChatRequest(message="anything"))
        try:
            parsed = uuid.UUID(result.session_id, version=4)
        except ValueError:
            pytest.fail(f"session_id is not a valid UUID4: {result.session_id!r}")
        assert str(parsed) == result.session_id

    async def test_http_status_error_logs_status_code_and_returns_fallback(self, service):
        """HTTPStatusError with a 503 body still routes to fallback (status code branch)."""
        exc = httpx.HTTPStatusError(
            "Service Unavailable",
            request=MagicMock(),
            response=MagicMock(),
        )
        exc.response.status_code = 503
        service._client.post = AsyncMock(side_effect=exc)
        result = await service.send_message(ChatRequest(message="test"))
        assert result.intent == "fallback"
        assert result.sources == ["fallback:service"]


# ============================================================================
# LLM SERVICE — _fallback_response branch prioritisation
# ============================================================================


class TestLLMFallbackResponseBranches:
    @pytest.fixture
    def service(self, settings):
        with patch("services.llm_service.httpx.AsyncClient"):
            return LLMService(settings)

    def _call(self, service, message: str) -> ChatResponse:
        return service._fallback_response(ChatRequest(message=message), session_id="test-sid")

    # --- emergency branch ---

    def test_emergency_takes_priority_over_challan_when_both_present(self, service):
        """'accident fine' — emergency terms are checked first, so intent is emergency."""
        result = self._call(service, "accident fine helmet")
        assert result.intent == "emergency"
        assert result.sources == ["fallback:emergency"]

    def test_sos_plus_challan_terms_still_emergency(self, service):
        """'sos challan section 185' — sos matches emergency first."""
        result = self._call(service, "sos challan section 185")
        assert result.intent == "emergency"

    def test_emergency_response_contains_112(self, service):
        """Emergency fallback must include the national emergency number 112."""
        result = self._call(service, "I had an accident")
        assert "112" in result.response

    def test_emergency_response_mentions_emergency_locator(self, service):
        """Emergency fallback references the emergency locator feature."""
        result = self._call(service, "I need an ambulance now")
        assert "emergency locator" in result.response.lower()

    def test_uppercase_emergency_term_matched_case_insensitively(self, service):
        """Message is lowercased before matching — AMBULANCE → ambulance."""
        result = self._call(service, "AMBULANCE NEEDED ASAP")
        assert result.intent == "emergency"

    # --- challan branch ---

    def test_challan_keyword_triggers_challan_intent(self, service):
        """Bare 'challan' keyword → challan intent."""
        result = self._call(service, "my challan status")
        assert result.intent == "challan"
        assert result.sources == ["fallback:challan"]

    def test_challan_response_mentions_calculator_endpoint(self, service):
        """Challan fallback text must reference the challan calculator."""
        result = self._call(service, "helmet fine amount please")
        assert "challan calculator" in result.response.lower()

    def test_mixed_case_fine_keyword_maps_to_challan(self, service):
        """'FINE' (upper) is lower()ed before matching → challan branch."""
        result = self._call(service, "What Is The FINE for speeding")
        assert result.intent == "challan"

    # --- generic fallback branch ---

    def test_unrecognised_query_returns_fallback_intent(self, service):
        """A message with no matching terms → fallback intent."""
        result = self._call(service, "what is the weather today")
        assert result.intent == "fallback"
        assert result.sources == ["fallback:service"]

    def test_fallback_response_mentions_warming_up(self, service):
        """Generic fallback text explains the service is warming up."""
        result = self._call(service, "random query")
        assert "warming up" in result.response.lower()

    def test_fallback_response_recommends_dedicated_tools(self, service):
        """Generic fallback recommends using the dedicated in-app tools."""
        result = self._call(service, "tell me about road rules")
        assert "tools" in result.response.lower()

    # --- session_id forwarding ---

    def test_session_id_forwarded_to_chat_response(self, service):
        """The session_id kwarg is surfaced verbatim in the returned ChatResponse."""
        result = service._fallback_response(
            ChatRequest(message="anything"), session_id="custom-sess-42"
        )
        assert result.session_id == "custom-sess-42"


# ============================================================================
# LLM SERVICE — aclose
# ============================================================================


class TestLLMServiceAcloseCoverage:
    async def test_aclose_awaits_http_client(self, settings):
        """aclose() must await the underlying httpx client's aclose()."""
        mock_client = AsyncMock()
        with patch("services.llm_service.httpx.AsyncClient", return_value=mock_client):
            svc = LLMService(settings)
        await svc.aclose()
        mock_client.aclose.assert_awaited_once()

    async def test_aclose_on_fresh_instance_does_not_raise(self, settings):
        """Calling aclose() immediately after construction must not raise."""
        with patch("services.llm_service.httpx.AsyncClient", return_value=AsyncMock()):
            svc = LLMService(settings)
        await svc.aclose()  # no exception expected


# ============================================================================
# SAFE ROUTING — _validate_coords (opposite overflow directions)
# ============================================================================


class TestValidateCoordsOppositeDirections:
    """The existing test file covers: origin lat -91, origin lon +181,
    dest lat +91, dest lon -181.  These cover the four complementary cases."""

    def test_origin_lat_too_high_positive(self):
        """Origin lat > 90 → ServiceValidationError."""
        with pytest.raises(ServiceValidationError, match="origin latitude 91"):
            _validate_coords((91.0, 0.0), (0.0, 0.0))

    def test_origin_lon_too_low_negative(self):
        """Origin lon < -180 → ServiceValidationError."""
        with pytest.raises(ServiceValidationError, match="origin longitude -181"):
            _validate_coords((0.0, -181.0), (0.0, 0.0))

    def test_dest_lat_too_low_negative(self):
        """Dest lat < -90 → ServiceValidationError."""
        with pytest.raises(ServiceValidationError, match="dest latitude -91"):
            _validate_coords((0.0, 0.0), (-91.0, 0.0))

    def test_dest_lon_too_high_positive(self):
        """Dest lon > 180 → ServiceValidationError."""
        with pytest.raises(ServiceValidationError, match="dest longitude 181"):
            _validate_coords((0.0, 0.0), (0.0, 181.0))

    def test_exact_boundary_values_are_accepted(self):
        """(-90, -180) → (90, 180) are legal boundary values — must not raise."""
        _validate_coords((-90.0, -180.0), (90.0, 180.0))

    def test_negative_lat_within_range_is_valid(self):
        """Negative latitude strictly within (-90, 0) range must not raise."""
        _validate_coords((-45.5, 77.59), (-12.93, 77.61))


# ============================================================================
# SAFE ROUTING — is_nighttime (boundary hours not in existing test file)
# ============================================================================


class TestIsNighttimeHourCoverage:
    @patch("services.safe_routing.datetime")
    def test_hour_7_is_daytime(self, mock_dt):
        """7am is one step above the nighttime cutoff (<=6) — must be False."""
        mock_dt.now.return_value.hour = 7
        assert is_nighttime() is False

    @patch("services.safe_routing.datetime")
    def test_hour_21_is_nighttime(self, mock_dt):
        """21:00 is inside the >=20 nighttime window — must be True."""
        mock_dt.now.return_value.hour = 21
        assert is_nighttime() is True

    @patch("services.safe_routing.datetime")
    def test_hour_1_is_nighttime(self, mock_dt):
        """1am is inside the <=6 early-morning window — must be True."""
        mock_dt.now.return_value.hour = 1
        assert is_nighttime() is True

    @patch("services.safe_routing.datetime")
    def test_hour_18_is_daytime(self, mock_dt):
        """18:00 (6pm) is before the >=20 nighttime threshold — must be False."""
        mock_dt.now.return_value.hour = 18
        assert is_nighttime() is False


# ============================================================================
# SAFE ROUTING — get_safe_route miscellaneous paths
# ============================================================================


class TestGetSafeRouteMiscPaths:
    @pytest.fixture
    def _osrm_mock_client(self):
        resp = MagicMock()
        resp.json.return_value = _OSRM_RESPONSE
        resp.raise_for_status.return_value = None
        client = AsyncMock()
        client.get.return_value = resp
        client.__aenter__.return_value = client
        return client

    @pytest.mark.asyncio
    async def test_prefer_safety_true_no_ors_key_uses_osrm_with_safety_mode(
        self, _osrm_mock_client
    ):
        """prefer_safety=True + no ORS key → safety_mode=True is forwarded to OSRM."""
        with (
            patch("services.safe_routing.os.getenv", return_value=""),
            patch("services.safe_routing.is_nighttime", return_value=False),
            patch("services.safe_routing.httpx.AsyncClient", return_value=_osrm_mock_client),
        ):
            result = await get_safe_route((12.97, 77.59), (12.93, 77.61), prefer_safety=True)
        assert result["provider"] == "osrm_fallback"
        assert result["safety_mode"] is True
        assert "without ORS key" in result["note"]

    @pytest.mark.asyncio
    async def test_prefer_safety_false_but_nighttime_sets_safety_mode(self, _osrm_mock_client):
        """prefer_safety=False + is_nighttime()=True → safety_mode=True via OR."""
        with (
            patch("services.safe_routing.os.getenv", return_value=""),
            patch("services.safe_routing.is_nighttime", return_value=True),
            patch("services.safe_routing.httpx.AsyncClient", return_value=_osrm_mock_client),
        ):
            result = await get_safe_route((12.97, 77.59), (12.93, 77.61))
        assert result["safety_mode"] is True

    @pytest.mark.asyncio
    async def test_coord_validation_runs_before_any_http_call(self):
        """Invalid coords raise ServiceValidationError without touching httpx."""
        with patch("services.safe_routing.httpx.AsyncClient") as mock_cls:
            with pytest.raises(ServiceValidationError):
                await get_safe_route((95.0, 0.0), (0.0, 0.0))
        mock_cls.assert_not_called()

    @pytest.mark.asyncio
    async def test_ors_routes_null_triggers_external_service_error(self):
        """ORS returns {'routes': null} → None[0] → TypeError → ExternalServiceError."""
        bad_resp = MagicMock()
        bad_resp.json.return_value = {"routes": None}
        bad_resp.raise_for_status.return_value = None
        mock_client = AsyncMock()
        mock_client.post.return_value = bad_resp
        mock_client.__aenter__.return_value = mock_client

        with (
            patch("services.safe_routing.os.getenv", return_value="ors-api-key"),
            patch("services.safe_routing.is_nighttime", return_value=False),
            patch("services.safe_routing.httpx.AsyncClient", return_value=mock_client),
        ):
            with pytest.raises(ExternalServiceError, match="Invalid response from ORS"):
                await get_safe_route((12.97, 77.59), (12.93, 77.61))

    @pytest.mark.asyncio
    async def test_osrm_routes_null_treated_as_empty_then_raises(self):
        """OSRM response {'routes': null} → `or []` → empty list → ExternalServiceError."""
        bad_resp = MagicMock()
        bad_resp.json.return_value = {"routes": None}
        bad_resp.raise_for_status.return_value = None
        mock_client = AsyncMock()
        mock_client.get.return_value = bad_resp
        mock_client.__aenter__.return_value = mock_client

        with (
            patch("services.safe_routing.os.getenv", return_value=""),
            patch("services.safe_routing.is_nighttime", return_value=False),
            patch("services.safe_routing.httpx.AsyncClient", return_value=mock_client),
        ):
            with pytest.raises(ExternalServiceError, match="No route found"):
                await get_safe_route((12.97, 77.59), (12.93, 77.61))


# ============================================================================
# SAFE ROUTING — _osrm_fallback called directly
# ============================================================================


class TestOsrmFallbackDirect:
    """Exercise _osrm_fallback in isolation to validate its own branches."""

    @pytest.fixture
    def _success_client(self):
        resp = MagicMock()
        resp.json.return_value = _OSRM_RESPONSE
        resp.raise_for_status.return_value = None
        client = AsyncMock()
        client.get.return_value = resp
        client.__aenter__.return_value = client
        return client

    @pytest.mark.asyncio
    async def test_missing_route_fields_default_to_zero_and_empty_dict(self):
        """Route dict without distance/duration/geometry → defaults (0, 0, {})."""
        resp = MagicMock()
        resp.json.return_value = {"routes": [{}]}  # empty route — no keys
        resp.raise_for_status.return_value = None
        client = AsyncMock()
        client.get.return_value = resp
        client.__aenter__.return_value = client

        with patch("services.safe_routing.httpx.AsyncClient", return_value=client):
            result = await _osrm_fallback((12.97, 77.59), (12.93, 77.61), safety_mode=False)

        assert result["distance_meters"] == 0
        assert result["duration_seconds"] == 0
        assert result["geometry"] == {}

    @pytest.mark.asyncio
    async def test_safety_mode_true_note_content(self, _success_client):
        """safety_mode=True → note warns that safety routing needs an ORS key."""
        with patch("services.safe_routing.httpx.AsyncClient", return_value=_success_client):
            result = await _osrm_fallback((12.97, 77.59), (12.93, 77.61), safety_mode=True)
        assert "without ORS key" in result["note"]
        assert result["safety_mode"] is True

    @pytest.mark.asyncio
    async def test_safety_mode_false_note_content(self, _success_client):
        """safety_mode=False → note is the standard OSRM message."""
        with patch("services.safe_routing.httpx.AsyncClient", return_value=_success_client):
            result = await _osrm_fallback((12.97, 77.59), (12.93, 77.61), safety_mode=False)
        assert result["note"] == "Standard OSRM route (no ORS key configured)."
        assert result["safety_mode"] is False

    @pytest.mark.asyncio
    async def test_provider_field_always_osrm_fallback(self, _success_client):
        """Successful _osrm_fallback always sets provider='osrm_fallback'."""
        with patch("services.safe_routing.httpx.AsyncClient", return_value=_success_client):
            result = await _osrm_fallback((12.97, 77.59), (12.93, 77.61), safety_mode=False)
        assert result["provider"] == "osrm_fallback"

    @pytest.mark.asyncio
    async def test_timeout_raises_external_service_error(self):
        """httpx.TimeoutException inside _osrm_fallback → ExternalServiceError."""
        client = AsyncMock()
        client.get.side_effect = httpx.TimeoutException("timed out")
        client.__aenter__.return_value = client

        with patch("services.safe_routing.httpx.AsyncClient", return_value=client):
            with pytest.raises(ExternalServiceError, match="Routing service unavailable"):
                await _osrm_fallback((12.97, 77.59), (12.93, 77.61), safety_mode=False)

    @pytest.mark.asyncio
    async def test_http_error_raises_external_service_error(self):
        """httpx.HTTPError inside _osrm_fallback → ExternalServiceError."""
        client = AsyncMock()
        client.get.side_effect = httpx.HTTPError("503 Service Unavailable")
        client.__aenter__.return_value = client

        with patch("services.safe_routing.httpx.AsyncClient", return_value=client):
            with pytest.raises(ExternalServiceError, match="Routing service unavailable"):
                await _osrm_fallback((12.97, 77.59), (12.93, 77.61), safety_mode=True)

    @pytest.mark.asyncio
    async def test_empty_routes_list_raises_external_service_error(self):
        """Empty routes list in OSRM response → ExternalServiceError."""
        resp = MagicMock()
        resp.json.return_value = {"routes": []}
        resp.raise_for_status.return_value = None
        client = AsyncMock()
        client.get.return_value = resp
        client.__aenter__.return_value = client

        with patch("services.safe_routing.httpx.AsyncClient", return_value=client):
            with pytest.raises(ExternalServiceError, match="No route found"):
                await _osrm_fallback((12.97, 77.59), (12.93, 77.61), safety_mode=False)


# ============================================================================
# SAFE SPACES — close_safe_spaces_client lifecycle
# ============================================================================


class TestCloseSafeSpacesClient:
    async def test_close_when_client_is_none_is_noop(self):
        """Closing when _CLIENT is None must not raise and must leave it None."""
        _ss_module._CLIENT = None
        await close_safe_spaces_client()
        assert _ss_module._CLIENT is None

    async def test_close_when_client_is_already_closed_skips_aclose(self):
        """If is_closed=True the function exits early without calling aclose()."""
        mock_client = MagicMock()
        mock_client.is_closed = True
        _ss_module._CLIENT = mock_client

        await close_safe_spaces_client()

        mock_client.aclose.assert_not_called()
        # _CLIENT is NOT reset to None in this branch (condition is False)
        assert _ss_module._CLIENT is mock_client

    async def test_close_open_client_awaits_aclose_and_resets_to_none(self):
        """An open client must have aclose() awaited and _CLIENT reset to None."""
        mock_client = AsyncMock()
        mock_client.is_closed = False
        _ss_module._CLIENT = mock_client

        await close_safe_spaces_client()

        mock_client.aclose.assert_awaited_once()
        assert _ss_module._CLIENT is None

    async def test_close_called_twice_second_call_is_noop(self):
        """Double-close: first call closes, second call (None) is a silent no-op."""
        mock_client = AsyncMock()
        mock_client.is_closed = False
        _ss_module._CLIENT = mock_client

        await close_safe_spaces_client()  # first: closes client, sets _CLIENT=None
        await close_safe_spaces_client()  # second: _CLIENT is None → no-op


# ============================================================================
# SAFE SPACES — radius_m validation (additional boundaries)
# ============================================================================


class TestGetSafeSpacesRadiusValidation:
    @pytest.mark.asyncio
    async def test_radius_none_bypasses_range_check(self):
        """radius_m=None satisfies the 'radius_m is not None' guard → no error raised."""
        mock_post = AsyncMock(return_value=_MockResponse(200, {"elements": []}))
        with patch("services.safe_spaces.httpx.AsyncClient.post", mock_post):
            result = await get_safe_spaces(13.0, 80.0, None)
        assert result["count"] == 0
        assert "warning" not in result

    @pytest.mark.asyncio
    async def test_radius_exactly_100_is_valid_lower_boundary(self):
        """radius_m=100 is the inclusive lower boundary — must not raise."""
        mock_post = AsyncMock(return_value=_MockResponse(200, {"elements": []}))
        with patch("services.safe_spaces.httpx.AsyncClient.post", mock_post):
            result = await get_safe_spaces(13.0, 80.0, 100)
        assert result["radius_meters"] == 100

    @pytest.mark.asyncio
    async def test_radius_exactly_100000_is_valid_upper_boundary(self):
        """radius_m=100_000 is the inclusive upper boundary — must not raise."""
        mock_post = AsyncMock(return_value=_MockResponse(200, {"elements": []}))
        with patch("services.safe_spaces.httpx.AsyncClient.post", mock_post):
            result = await get_safe_spaces(13.0, 80.0, 100000)
        assert result["radius_meters"] == 100000

    @pytest.mark.asyncio
    async def test_radius_50_is_below_minimum(self):
        """radius_m=50 is below the 100-minimum → ServiceValidationError."""
        with pytest.raises(ServiceValidationError, match="Invalid radius"):
            await get_safe_spaces(13.0, 80.0, 50)

    @pytest.mark.asyncio
    async def test_radius_100001_is_above_maximum(self):
        """radius_m=100_001 is above the 100_000-maximum → ServiceValidationError."""
        with pytest.raises(ServiceValidationError, match="Invalid radius"):
            await get_safe_spaces(13.0, 80.0, 100001)

    @pytest.mark.asyncio
    async def test_lat_boundary_90_is_valid(self):
        """lat=90.0 is the inclusive upper boundary — must not raise."""
        mock_post = AsyncMock(return_value=_MockResponse(200, {"elements": []}))
        with patch("services.safe_spaces.httpx.AsyncClient.post", mock_post):
            result = await get_safe_spaces(90.0, 0.0, 1000)
        assert result["count"] == 0

    @pytest.mark.asyncio
    async def test_lon_boundary_minus_180_is_valid(self):
        """lon=-180.0 is the inclusive lower boundary — must not raise."""
        mock_post = AsyncMock(return_value=_MockResponse(200, {"elements": []}))
        with patch("services.safe_spaces.httpx.AsyncClient.post", mock_post):
            result = await get_safe_spaces(0.0, -180.0, 1000)
        assert result["count"] == 0


# ============================================================================
# SAFE SPACES — HTTP status-code branches not covered by existing tests
# ============================================================================


class TestGetSafeSpacesHTTPStatusBranches:
    @pytest.mark.asyncio
    async def test_status_400_is_skipped_by_generic_ge_400_branch(self):
        """400 is >= 400 but NOT in (406, 429, 503) — falls through to the
        generic 'if r.status_code >= 400: continue' branch."""
        mock_post = AsyncMock(
            side_effect=[
                _MockResponse(400, {}),
                _MockResponse(200, {"elements": _SAMPLE_ELEMENTS}),
            ]
        )
        with patch("services.safe_spaces.httpx.AsyncClient.post", mock_post):
            result = await get_safe_spaces(13.0, 80.0, 1000)
        assert result["count"] == len(_SAMPLE_ELEMENTS)
        assert "warning" not in result
        assert mock_post.call_count == 2

    @pytest.mark.asyncio
    async def test_status_500_is_skipped_by_generic_ge_400_branch(self):
        """500 hits the same 'status_code >= 400' continue path as 400."""
        mock_post = AsyncMock(
            side_effect=[
                _MockResponse(500, {}),
                _MockResponse(200, {"elements": _SAMPLE_ELEMENTS}),
            ]
        )
        with patch("services.safe_spaces.httpx.AsyncClient.post", mock_post):
            result = await get_safe_spaces(13.0, 80.0, 1000)
        assert result["count"] == len(_SAMPLE_ELEMENTS)
        assert mock_post.call_count == 2

    @pytest.mark.asyncio
    async def test_all_three_endpoints_return_400_produces_warning(self):
        """All three endpoints returning 400 → graceful empty response with warning."""
        mock_post = AsyncMock(return_value=_MockResponse(400, {}))
        with patch("services.safe_spaces.httpx.AsyncClient.post", mock_post):
            result = await get_safe_spaces(13.0, 80.0, 1000)
        assert result["count"] == 0
        assert result["places"] == []
        assert "warning" in result
        assert mock_post.call_count == 3

    @pytest.mark.asyncio
    async def test_warning_message_mentions_overpass_rate_limit(self):
        """The fallback warning explicitly mentions the Overpass API rate limit."""
        mock_post = AsyncMock(return_value=_MockResponse(429, {}))
        with patch("services.safe_spaces.httpx.AsyncClient.post", mock_post):
            result = await get_safe_spaces(13.0, 80.0, 1000)
        warning = result["warning"].lower()
        assert "overpass" in warning
        assert "rate limit" in warning


# ============================================================================
# SAFE SPACES — element tag mapping branches
# ============================================================================


class TestGetSafeSpacesTagMapping:
    @pytest.mark.asyncio
    async def test_contact_phone_tag_used_when_phone_absent(self):
        """When 'phone' tag is absent, 'contact:phone' is the fallback source."""
        elements = [
            {
                "type": "node",
                "id": 1,
                "lat": 13.0,
                "lon": 80.0,
                "tags": {
                    "name": "General Clinic",
                    "amenity": "hospital",
                    "contact:phone": "+91-80-12345678",
                },
            }
        ]
        mock_post = AsyncMock(return_value=_MockResponse(200, {"elements": elements}))
        with patch("services.safe_spaces.httpx.AsyncClient.post", mock_post):
            result = await get_safe_spaces(13.0, 80.0, 1000)
        assert result["places"][0]["phone"] == "+91-80-12345678"

    @pytest.mark.asyncio
    async def test_shop_tag_used_as_type_when_amenity_absent(self):
        """When 'amenity' tag is absent, 'shop' tag provides the 'type' field."""
        elements = [
            {
                "type": "node",
                "id": 1,
                "lat": 13.0,
                "lon": 80.0,
                "tags": {"name": "Quick Mart", "shop": "convenience"},
            }
        ]
        mock_post = AsyncMock(return_value=_MockResponse(200, {"elements": elements}))
        with patch("services.safe_spaces.httpx.AsyncClient.post", mock_post):
            result = await get_safe_spaces(13.0, 80.0, 1000)
        assert result["places"][0]["type"] == "convenience"

    @pytest.mark.asyncio
    async def test_type_defaults_to_place_when_neither_amenity_nor_shop(self):
        """When neither 'amenity' nor 'shop' tag is present, type defaults to 'place'."""
        elements = [
            {
                "type": "node",
                "id": 1,
                "lat": 13.0,
                "lon": 80.0,
                "tags": {"name": "Mystery Node"},
            }
        ]
        mock_post = AsyncMock(return_value=_MockResponse(200, {"elements": elements}))
        with patch("services.safe_spaces.httpx.AsyncClient.post", mock_post):
            result = await get_safe_spaces(13.0, 80.0, 1000)
        assert result["places"][0]["type"] == "place"

    @pytest.mark.asyncio
    async def test_elements_without_lat_lon_are_filtered_out(self):
        """Elements missing lat/lon keys are excluded from the places list."""
        elements = [
            {
                "type": "node",
                "id": 1,
                "lat": 13.0,
                "lon": 80.0,
                "tags": {"name": "Has Coords", "amenity": "cafe"},
            },
            {
                "type": "node",
                "id": 2,
                "tags": {"name": "No Coords"},  # no lat/lon
            },
        ]
        mock_post = AsyncMock(return_value=_MockResponse(200, {"elements": elements}))
        with patch("services.safe_spaces.httpx.AsyncClient.post", mock_post):
            result = await get_safe_spaces(13.0, 80.0, 1000)
        assert result["count"] == 1
        assert result["places"][0]["name"] == "Has Coords"

    @pytest.mark.asyncio
    async def test_empty_elements_list_succeeds_without_warning(self):
        """An endpoint returning elements=[] is a valid success — no warning key."""
        mock_post = AsyncMock(return_value=_MockResponse(200, {"elements": []}))
        with patch("services.safe_spaces.httpx.AsyncClient.post", mock_post):
            result = await get_safe_spaces(13.0, 80.0, 1000)
        assert result["count"] == 0
        assert result["places"] == []
        assert result["source"] == "openstreetmap"
        assert "warning" not in result

    @pytest.mark.asyncio
    async def test_opening_hours_is_none_when_tag_absent(self):
        """Absent 'opening_hours' tag → open_hours field is None."""
        elements = [
            {
                "type": "node",
                "id": 1,
                "lat": 13.0,
                "lon": 80.0,
                "tags": {"name": "Night Cafe", "amenity": "cafe"},
            }
        ]
        mock_post = AsyncMock(return_value=_MockResponse(200, {"elements": elements}))
        with patch("services.safe_spaces.httpx.AsyncClient.post", mock_post):
            result = await get_safe_spaces(13.0, 80.0, 1000)
        assert result["places"][0]["open_hours"] is None

    @pytest.mark.asyncio
    async def test_phone_is_none_when_both_phone_and_contact_phone_absent(self):
        """Neither 'phone' nor 'contact:phone' present → phone field is None."""
        elements = [
            {
                "type": "node",
                "id": 1,
                "lat": 13.0,
                "lon": 80.0,
                "tags": {"name": "Silent Node", "amenity": "police"},
            }
        ]
        mock_post = AsyncMock(return_value=_MockResponse(200, {"elements": elements}))
        with patch("services.safe_spaces.httpx.AsyncClient.post", mock_post):
            result = await get_safe_spaces(13.0, 80.0, 1000)
        assert result["places"][0]["phone"] is None

    @pytest.mark.asyncio
    async def test_result_always_has_radius_meters_and_source_keys(self):
        """Both success and fallback dicts expose radius_meters and source."""
        mock_post = AsyncMock(return_value=_MockResponse(200, {"elements": _SAMPLE_ELEMENTS}))
        with patch("services.safe_spaces.httpx.AsyncClient.post", mock_post):
            result = await get_safe_spaces(13.0, 80.0, 500)
        assert result["radius_meters"] == 500
        assert result["source"] == "openstreetmap"
