# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

from unittest.mock import ANY, AsyncMock, MagicMock, patch

import httpx
import pytest

from config import Settings
from tools import BackendToolClient
from tools.geocoding import GeocodingClient
from tools.legal_search_tool import LegalSearchTool
from tools.road_infra_tool import RoadInfrastructureTool
from tools.road_issues_tool import RoadIssuesTool
from tools.sos_tool import SosTool
from tools.what3words import What3WordsTool
from rag.retriever import RetrievalResult, Retriever


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_settings() -> MagicMock:
    s = MagicMock(spec=Settings)
    s.main_backend_base_url = "http://test-backend:8000"
    s.main_backend_timeout_seconds = 20.0
    s.http_user_agent = "SafeVixAIChatbot/1.0"
    s.internal_api_key = None
    return s


def _make_httpx_client(get_ret: ANY = None, post_ret: ANY = None) -> AsyncMock:
    """Return an AsyncMock(spec=httpx.AsyncClient) with get/post configured."""
    c = AsyncMock(spec=httpx.AsyncClient)
    if get_ret is not None:
        c.get = AsyncMock(return_value=get_ret)
    if post_ret is not None:
        c.post = AsyncMock(return_value=post_ret)
    return c


def _http_status_error(status: int, message: str = "Error") -> httpx.HTTPStatusError:
    resp = MagicMock()
    resp.status_code = status
    return httpx.HTTPStatusError(message, request=MagicMock(), response=resp)


# ===================================================================
# BackendToolClient
# ===================================================================

class TestBackendToolClient:

    def test_constructor_creates_client_with_correct_config(self):
        settings = _make_settings()
        with patch('tools.httpx.AsyncClient') as mock_cls:
            BackendToolClient(settings)
            mock_cls.assert_called_once_with(
                base_url="http://test-backend:8000",
                timeout=20.0,
                headers={
                    'Accept': 'application/json',
                    'User-Agent': 'SafeVixAIChatbot/1.0',
                },
            )

    @pytest.mark.asyncio
    async def test_get_returns_dict_on_success(self):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"key": "value"}
        settings = _make_settings()
        client = _make_httpx_client(get_ret=mock_resp)

        with patch('tools.httpx.AsyncClient', return_value=client):
            bc = BackendToolClient(settings)
            result = await bc.get("/path", params={"q": "1"})

            assert result == {"key": "value"}
            client.get.assert_awaited_once_with("/path", params={"q": "1"})

    @pytest.mark.asyncio
    async def test_get_without_params_passes_none_to_httpx(self):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {}
        settings = _make_settings()
        client = _make_httpx_client(get_ret=mock_resp)

        with patch('tools.httpx.AsyncClient', return_value=client):
            bc = BackendToolClient(settings)
            result = await bc.get("/path")

            assert result == {}
            client.get.assert_awaited_once_with("/path", params=None)

    @pytest.mark.asyncio
    async def test_get_http_4xx_returns_none_without_alert(self):
        alert = MagicMock()
        exc = _http_status_error(404, "Not Found")
        settings = _make_settings()
        client = _make_httpx_client()
        client.get = AsyncMock(side_effect=exc)

        with patch('tools.httpx.AsyncClient', return_value=client), \
             patch('tools.get_alert_service', return_value=alert):
            bc = BackendToolClient(settings)
            result = await bc.get("/path")

            assert result is None
            alert.alert_external_api_failed.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_http_5xx_triggers_alert(self):
        alert = MagicMock()
        exc = _http_status_error(502, "Bad Gateway")
        settings = _make_settings()
        client = _make_httpx_client()
        client.get = AsyncMock(side_effect=exc)

        with patch('tools.httpx.AsyncClient', return_value=client), \
             patch('tools.get_alert_service', return_value=alert):
            bc = BackendToolClient(settings)
            result = await bc.get("/path")

            assert result is None
            alert.alert_external_api_failed.assert_called_once_with(
                service_name="Backend API",
                endpoint="GET /path",
                status_code=502,
                error_msg=ANY,
            )

    @pytest.mark.asyncio
    async def test_get_request_error_triggers_alert(self):
        alert = MagicMock()
        exc = httpx.RequestError("Connection refused")
        settings = _make_settings()
        client = _make_httpx_client()
        client.get = AsyncMock(side_effect=exc)

        with patch('tools.httpx.AsyncClient', return_value=client), \
             patch('tools.get_alert_service', return_value=alert):
            bc = BackendToolClient(settings)
            result = await bc.get("/path")

            assert result is None
            alert.alert_external_api_failed.assert_called_once_with(
                service_name="Backend API",
                endpoint="GET /path",
                status_code=0,
                error_msg=ANY,
            )

    @pytest.mark.asyncio
    async def test_get_value_error_returns_none(self):
        mock_resp = MagicMock()
        mock_resp.json.side_effect = ValueError("bad json")
        settings = _make_settings()
        client = _make_httpx_client(get_ret=mock_resp)

        with patch('tools.httpx.AsyncClient', return_value=client):
            bc = BackendToolClient(settings)
            result = await bc.get("/path")

            assert result is None

    @pytest.mark.asyncio
    async def test_post_returns_dict_on_success(self):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"id": 42}
        settings = _make_settings()
        client = _make_httpx_client(post_ret=mock_resp)

        with patch('tools.httpx.AsyncClient', return_value=client):
            bc = BackendToolClient(settings)
            result = await bc.post("/path", payload={"name": "test"})

            assert result == {"id": 42}
            client.post.assert_awaited_once_with("/path", json={"name": "test"})

    @pytest.mark.asyncio
    async def test_post_with_empty_payload(self):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {}
        settings = _make_settings()
        client = _make_httpx_client(post_ret=mock_resp)

        with patch('tools.httpx.AsyncClient', return_value=client):
            bc = BackendToolClient(settings)
            result = await bc.post("/path", payload={})

            assert result == {}
            client.post.assert_awaited_once_with("/path", json={})

    @pytest.mark.asyncio
    async def test_post_http_4xx_returns_none(self):
        alert = MagicMock()
        exc = _http_status_error(400, "Bad Request")
        settings = _make_settings()
        client = _make_httpx_client()
        client.post = AsyncMock(side_effect=exc)

        with patch('tools.httpx.AsyncClient', return_value=client), \
             patch('tools.get_alert_service', return_value=alert):
            bc = BackendToolClient(settings)
            result = await bc.post("/path")

            assert result is None
            alert.alert_external_api_failed.assert_not_called()

    @pytest.mark.asyncio
    async def test_post_http_5xx_triggers_alert(self):
        alert = MagicMock()
        exc = _http_status_error(500, "Server Error")
        settings = _make_settings()
        client = _make_httpx_client()
        client.post = AsyncMock(side_effect=exc)

        with patch('tools.httpx.AsyncClient', return_value=client), \
             patch('tools.get_alert_service', return_value=alert):
            bc = BackendToolClient(settings)
            result = await bc.post("/path")

            assert result is None
            alert.alert_external_api_failed.assert_called_once_with(
                service_name="Backend API",
                endpoint="POST /path",
                status_code=500,
                error_msg=ANY,
            )

    @pytest.mark.asyncio
    async def test_post_request_error_triggers_alert(self):
        alert = MagicMock()
        exc = httpx.RequestError("Timeout")
        settings = _make_settings()
        client = _make_httpx_client()
        client.post = AsyncMock(side_effect=exc)

        with patch('tools.httpx.AsyncClient', return_value=client), \
             patch('tools.get_alert_service', return_value=alert):
            bc = BackendToolClient(settings)
            result = await bc.post("/path")

            assert result is None
            alert.alert_external_api_failed.assert_called_once_with(
                service_name="Backend API",
                endpoint="POST /path",
                status_code=0,
                error_msg=ANY,
            )

    @pytest.mark.asyncio
    async def test_post_value_error_returns_none(self):
        mock_resp = MagicMock()
        mock_resp.json.side_effect = ValueError("bad json")
        settings = _make_settings()
        client = _make_httpx_client(post_ret=mock_resp)

        with patch('tools.httpx.AsyncClient', return_value=client):
            bc = BackendToolClient(settings)
            result = await bc.post("/path")

            assert result is None

    @pytest.mark.asyncio
    async def test_aclose_closes_underlying_client(self):
        settings = _make_settings()
        client = _make_httpx_client()

        with patch('tools.httpx.AsyncClient', return_value=client):
            bc = BackendToolClient(settings)
            await bc.aclose()

            client.aclose.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_raises_after_aclose(self):
        settings = _make_settings()
        client = _make_httpx_client()

        with patch('tools.httpx.AsyncClient', return_value=client):
            bc = BackendToolClient(settings)
            await bc.aclose()

            client.aclose.assert_awaited_once()
            client.get.assert_not_awaited()


# ===================================================================
# SosTool
# ===================================================================

class TestSosTool:

    @pytest.fixture
    def mock_backend(self) -> AsyncMock:
        return AsyncMock(spec=BackendToolClient)

    @pytest.fixture
    def mock_w3w(self) -> AsyncMock:
        return AsyncMock(spec=What3WordsTool)

    @pytest.fixture
    def mock_geocode(self) -> AsyncMock:
        return AsyncMock(spec=GeocodingClient)

    @pytest.fixture
    def sos_tool(self, mock_backend: AsyncMock, mock_w3w: AsyncMock,
                 mock_geocode: AsyncMock) -> SosTool:
        return SosTool(
            backend_client=mock_backend,
            w3w_tool=mock_w3w,
            geocode_client=mock_geocode,
        )

    def test_constructor_stores_dependencies(self, mock_backend: AsyncMock,
                                             mock_w3w: AsyncMock,
                                             mock_geocode: AsyncMock):
        tool = SosTool(
            backend_client=mock_backend,
            w3w_tool=mock_w3w,
            geocode_client=mock_geocode,
        )
        assert tool.backend_client is mock_backend
        assert tool.w3w is mock_w3w
        assert tool.geocode is mock_geocode

    @pytest.mark.asyncio
    async def test_get_payload_all_succeed_returns_merged_payload(
        self, sos_tool: SosTool, mock_backend: AsyncMock, mock_w3w: AsyncMock,
        mock_geocode: AsyncMock,
    ):
        mock_backend.get.return_value = {"sos": "data", "services": ["hospital"]}
        mock_w3w.gps_to_words.return_value = {"words": "filled.count.soap"}
        mock_geocode.reverse_geocode.return_value = {"display": "Chennai, TN"}

        result = await sos_tool.get_payload(lat=13.0, lon=80.0)

        assert result == {
            "sos": "data",
            "services": ["hospital"],
            "what3words": {"words": "filled.count.soap"},
            "address": {"display": "Chennai, TN"},
        }
        mock_backend.get.assert_awaited_once_with(
            '/api/v1/emergency/sos', params={'lat': 13.0, 'lon': 80.0},
        )
        mock_w3w.gps_to_words.assert_awaited_once_with(lat=13.0, lon=80.0)
        mock_geocode.reverse_geocode.assert_awaited_once_with(lat=13.0, lon=80.0)

    @pytest.mark.asyncio
    async def test_get_payload_backend_fails_returns_none(
        self, sos_tool: SosTool, mock_backend: AsyncMock,
    ):
        mock_backend.get.return_value = None

        result = await sos_tool.get_payload(lat=13.0, lon=80.0)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_payload_backend_succeeds_w3w_fails_payload_without_w3w(
        self, sos_tool: SosTool, mock_backend: AsyncMock, mock_w3w: AsyncMock,
        mock_geocode: AsyncMock,
    ):
        mock_backend.get.return_value = {"services": ["hospital"]}
        mock_w3w.gps_to_words.return_value = None
        mock_geocode.reverse_geocode.return_value = {"display": "Chennai"}

        result = await sos_tool.get_payload(lat=13.0, lon=80.0)

        assert result == {
            "services": ["hospital"],
            "address": {"display": "Chennai"},
        }
        assert "what3words" not in result

    @pytest.mark.asyncio
    async def test_get_payload_backend_succeeds_geocode_fails_payload_without_address(
        self, sos_tool: SosTool, mock_backend: AsyncMock, mock_w3w: AsyncMock,
        mock_geocode: AsyncMock,
    ):
        mock_backend.get.return_value = {"services": ["hospital"]}
        mock_w3w.gps_to_words.return_value = {"words": "filled.count.soap"}
        mock_geocode.reverse_geocode.return_value = None

        result = await sos_tool.get_payload(lat=13.0, lon=80.0)

        assert result == {
            "services": ["hospital"],
            "what3words": {"words": "filled.count.soap"},
        }
        assert "address" not in result


# ===================================================================
# ===================================================================
# RoadInfrastructureTool
# ===================================================================

class TestRoadInfrastructureTool:

    def test_constructor_stores_backend_client(self):
        backend = MagicMock(spec=BackendToolClient)
        tool = RoadInfrastructureTool(backend_client=backend)
        assert tool.backend_client is backend

    @pytest.mark.asyncio
    async def test_lookup_returns_dict_on_success(self):
        backend = AsyncMock(spec=BackendToolClient)
        backend.get.return_value = {"roads": [], "contractors": []}
        tool = RoadInfrastructureTool(backend_client=backend)

        result = await tool.lookup(lat=13.0, lon=80.0)

        assert result == {"roads": [], "contractors": []}
        backend.get.assert_awaited_once_with(
            '/api/v1/roads/infrastructure',
            params={'lat': 13.0, 'lon': 80.0},
        )

    @pytest.mark.asyncio
    async def test_lookup_backend_fails_returns_none(self):
        backend = AsyncMock(spec=BackendToolClient)
        backend.get.return_value = None
        tool = RoadInfrastructureTool(backend_client=backend)

        result = await tool.lookup(lat=13.0, lon=80.0)

        assert result is None


# ===================================================================
# RoadIssuesTool
# ===================================================================

class TestRoadIssuesTool:

    def test_constructor_stores_backend_client(self):
        backend = MagicMock(spec=BackendToolClient)
        tool = RoadIssuesTool(backend_client=backend)
        assert tool.backend_client is backend

    @pytest.mark.asyncio
    async def test_lookup_returns_dict_on_success(self):
        backend = AsyncMock(spec=BackendToolClient)
        backend.get.return_value = {"issues": [{"type": "pothole"}]}
        tool = RoadIssuesTool(backend_client=backend)

        result = await tool.lookup(lat=13.0, lon=80.0, radius=5000, limit=5)

        assert result == {"issues": [{"type": "pothole"}]}
        backend.get.assert_awaited_once_with(
            '/api/v1/roads/issues',
            params={'lat': 13.0, 'lon': 80.0, 'radius': 5000, 'limit': 5},
        )

    @pytest.mark.asyncio
    async def test_lookup_backend_fails_returns_none(self):
        backend = AsyncMock(spec=BackendToolClient)
        backend.get.return_value = None
        tool = RoadIssuesTool(backend_client=backend)

        result = await tool.lookup(lat=13.0, lon=80.0)

        assert result is None

    @pytest.mark.asyncio
    async def test_lookup_uses_default_radius_and_limit(self):
        backend = AsyncMock(spec=BackendToolClient)
        backend.get.return_value = {"issues": []}
        tool = RoadIssuesTool(backend_client=backend)

        result = await tool.lookup(lat=13.0, lon=80.0)

        assert result == {"issues": []}
        backend.get.assert_awaited_once_with(
            '/api/v1/roads/issues',
            params={'lat': 13.0, 'lon': 80.0, 'radius': 5000, 'limit': 5},
        )


# ===================================================================
# LegalSearchTool
# ===================================================================

class TestLegalSearchTool:

    def test_constructor_stores_retriever(self):
        retriever = MagicMock(spec=Retriever)
        tool = LegalSearchTool(retriever=retriever)
        assert tool.retriever is retriever

    @pytest.mark.asyncio
    async def test_search_returns_results_from_retriever(self):
        retriever = MagicMock(spec=Retriever)
        expected = [
            RetrievalResult(
                source="mva.pdf",
                title="Section 185",
                category="legal",
                content="Drunk driving penalty...",
                score=0.92,
            ),
        ]
        retriever.retrieve.return_value = expected
        tool = LegalSearchTool(retriever=retriever)
    
        results = await tool.search("drunk driving", top_k=4)
    
        assert results == expected
        retriever.retrieve.assert_called_once_with(
            "drunk driving", top_k=4, scopes={'legal'},
        )

    @pytest.mark.asyncio
    async def test_search_empty_results_returns_empty_list(self):
        retriever = MagicMock(spec=Retriever)
        retriever.retrieve.return_value = []
        tool = LegalSearchTool(retriever=retriever)
    
        results = await tool.search("non existent law")
    
        assert results == []
        retriever.retrieve.assert_called_once_with(
            "non existent law", top_k=4, scopes={'legal'},
        )
