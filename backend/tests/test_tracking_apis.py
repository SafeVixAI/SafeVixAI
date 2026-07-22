# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

import uuid
from datetime import datetime
from unittest.mock import ANY, AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.v1.tracking import (
    ConnectionHealth,
    RedisConnectionManager,
    _is_valid_location,
    _is_valid_tracking_payload,
    _origin_allowed,
)
from core.limiter import limiter


@pytest.fixture(autouse=True)
def disable_limiter():
    limiter.enabled = False
    yield


# ── Helper ──────────────────────────────────────────────────────────────────

def _make_async_session_mock():
    """Create a mock session that works with async for pattern."""
    session = AsyncMock()
    session.execute = AsyncMock()
    result = MagicMock()
    result.fetchone = MagicMock()
    session.execute.return_value = result
    return session


async def _async_gen(*args, **kwargs):
    """Async generator that yields a mock session."""
    yield _make_async_session_mock()


# ── live_tracking.py REST tests ─────────────────────────────────────────────

@pytest.fixture
def live_tracking_app():
    app = FastAPI()
    from api.v1.live_tracking import get_current_user, router
    app.include_router(router)
    app.dependency_overrides[get_current_user] = lambda: {"sub": "user-1", "email": "test@test.com"}
    return app


class TestLiveTrackingAPI:
    def test_start_tracking_success(self, live_tracking_app):
        client = TestClient(live_tracking_app)
        with patch("api.v1.live_tracking.get_async_session", _async_gen):
            with patch("api.v1.live_tracking.create_access_token", return_value="test-token"):
                with patch("api.v1.live_tracking.get_settings") as s:
                    s.return_value.frontend_url = "http://localhost:3000"
                    s.return_value.cors_origins = ["*"]
                    response = client.post(
                        "/api/v1/live-tracking/start",
                        json={
                            "user_name": "Test User",
                            "blood_group": "O+",
                            "vehicle_number": "TN-01-AB-1234",
                            "latitude": 13.0827,
                            "longitude": 80.2707,
                            "battery_percent": 85,
                        },
                    )
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert "tracking_url" in data
        assert "expires_at" in data
        assert "test-token" in data["tracking_url"]

    def test_start_tracking_minimal(self, live_tracking_app):
        client = TestClient(live_tracking_app)
        with patch("api.v1.live_tracking.get_async_session", _async_gen):
            with patch("api.v1.live_tracking.create_access_token", return_value="tok"):
                with patch("api.v1.live_tracking.get_settings") as s:
                    s.return_value.frontend_url = ""
                    s.return_value.cors_origins = []
                    response = client.post(
                        "/api/v1/live-tracking/start",
                        json={"user_name": "U", "latitude": 0, "longitude": 0},
                    )
        assert response.status_code == 200

    def test_update_location_success(self, live_tracking_app):
        client = TestClient(live_tracking_app)
        with patch("api.v1.live_tracking.get_async_session", _async_gen):
            response = client.put(
                "/api/v1/live-tracking/update",
                json={
                    "session_id": str(uuid.uuid4()),
                    "latitude": 13.0,
                    "longitude": 80.0,
                    "accuracy": 10.0,
                    "speed_kmh": 30.5,
                    "battery_percent": 70,
                },
            )
        assert response.status_code == 200

    def test_update_location_not_found(self, live_tracking_app):
        client = TestClient(live_tracking_app)
        session = _make_async_session_mock()
        session.execute.return_value.fetchone.return_value = None

        async def gen_no_result():
            yield session

        with patch("api.v1.live_tracking.get_async_session", gen_no_result):
            response = client.put(
                "/api/v1/live-tracking/update",
                json={
                    "session_id": str(uuid.uuid4()),
                    "latitude": 13.0,
                    "longitude": 80.0,
                },
            )
        assert response.status_code == 404

    def test_get_session_public_valid_token(self, live_tracking_app):
        client = TestClient(live_tracking_app)
        session = _make_async_session_mock()
        sid = uuid.uuid4()
        sid_str = str(sid)
        row = MagicMock()
        row.session_id = sid_str
        row.user_name = "U"
        row.blood_group = "O+"
        row.vehicle_number = "TN01"
        row.latitude = 13.0
        row.longitude = 80.0
        row.accuracy = None
        row.speed_kmh = None
        row.battery_percent = 85
        row.is_active = True
        row.updated_at = datetime(2026, 1, 1, 0, 0, 0)
        session.execute.return_value.fetchone.return_value = row

        async def gen_with_row():
            yield session

        with patch("api.v1.live_tracking.get_async_session", gen_with_row):
            with patch("api.v1.live_tracking.jwt.decode") as mock_decode:
                mock_decode.return_value = {"sub": sid_str, "purpose": "tracking_view"}
                response = client.get(
                    f"/api/v1/live-tracking/session/{sid_str}",
                    params={"token": "x" * 20},
                )
        assert response.status_code == 200
        assert response.json()["user_name"] == "U"

    def test_get_session_no_token_returns_403(self, live_tracking_app):
        client = TestClient(live_tracking_app)
        sid = uuid.uuid4()
        with patch("api.v1.live_tracking.get_async_session", _async_gen):
            response = client.get(f"/api/v1/live-tracking/session/{sid}")
        assert response.status_code in (403, 422)

    def test_stop_tracking_success(self, live_tracking_app):
        client = TestClient(live_tracking_app)
        sid = uuid.uuid4()
        with patch("api.v1.live_tracking.get_async_session", _async_gen):
            response = client.delete(f"/api/v1/live-tracking/session/{sid}")
        assert response.status_code in (200, 404)

    def test_stop_tracking_not_found(self, live_tracking_app):
        client = TestClient(live_tracking_app)
        session = _make_async_session_mock()
        session.execute.return_value.fetchone.return_value = None

        async def gen_no():
            yield session

        with patch("api.v1.live_tracking.get_async_session", gen_no):
            sid = uuid.uuid4()
            response = client.delete(f"/api/v1/live-tracking/session/{sid}")
        assert response.status_code == 404


# ── tracking.py helper tests ────────────────────────────────────────────────

class TestTrackingHelpers:
    def test_is_valid_location_none(self):
        assert _is_valid_location(None, minimum=-90, maximum=90) is True

    def test_is_valid_location_valid(self):
        assert _is_valid_location(13.0, minimum=-90, maximum=90) is True

    def test_is_valid_location_invalid_type(self):
        assert _is_valid_location("abc", minimum=-90, maximum=90) is False

    def test_is_valid_location_out_of_range(self):
        assert _is_valid_location(100, minimum=-90, maximum=90) is False

    def test_is_valid_payload_valid(self):
        assert _is_valid_tracking_payload({"lat": 13.0, "lon": 80.0}) is True

    def test_is_valid_payload_with_latitude_alias(self):
        assert _is_valid_tracking_payload({"latitude": 13.0, "longitude": 80.0}) is True

    def test_is_valid_payload_not_dict(self):
        assert _is_valid_tracking_payload("not a dict") is False

    def test_is_valid_payload_empty_dict(self):
        assert _is_valid_tracking_payload({}) is False

    def test_is_valid_payload_invalid_coords(self):
        assert _is_valid_tracking_payload({"lat": 999, "lon": 80}) is False

    def test_origin_allowed_wildcard_production(self):
        with patch("api.v1.tracking.get_settings") as s:
            s.return_value.cors_origins = ["*"]
            s.return_value.environment = "production"
            assert _origin_allowed("https://evil.com") is False

    def test_origin_allowed_wildcard_non_production(self):
        with patch("api.v1.tracking.get_settings") as s:
            s.return_value.cors_origins = ["*"]
            s.return_value.environment = "development"
            assert _origin_allowed("https://evil.com") is True

    def test_origin_allowed_specific_origin(self):
        with patch("api.v1.tracking.get_settings") as s:
            s.return_value.cors_origins = ["https://app.safevixai.com"]
            s.return_value.environment = "production"
            assert _origin_allowed("https://app.safevixai.com") is True
            assert _origin_allowed("https://evil.com") is False

    def test_origin_allowed_none_development(self):
        with patch("api.v1.tracking.get_settings") as s:
            s.return_value.cors_origins = []
            s.return_value.environment = "development"
            assert _origin_allowed(None) is True

    def test_origin_allowed_none_production(self):
        with patch("api.v1.tracking.get_settings") as s:
            s.return_value.cors_origins = []
            s.return_value.environment = "production"
            assert _origin_allowed(None) is False


class TestConnectionHealth:
    def test_mark_activity(self):
        ch = ConnectionHealth()
        ws = MagicMock()
        ch.mark_activity(ws)
        assert id(ws) in ch._last_activity

    def test_remove(self):
        ch = ConnectionHealth()
        ws = MagicMock()
        ch.mark_activity(ws)
        ch.remove(ws)
        assert id(ws) not in ch._last_activity

    def test_stale_connections(self):
        ch = ConnectionHealth()
        ws1 = MagicMock()
        ws2 = MagicMock()
        ch.mark_activity(ws1)
        ch._last_activity[id(ws1)] = 100.0
        ch.mark_activity(ws2)
        ch._last_activity[id(ws2)] = 1000.0
        with patch("api.v1.tracking.time.monotonic", return_value=1000.0):
            stale = ch.stale_connections({ws1, ws2}, timeout=500)
            assert ws1 in stale
            assert ws2 not in stale

    def test_stale_connections_no_activity(self):
        ch = ConnectionHealth()
        ws = MagicMock()
        stale = ch.stale_connections({ws}, timeout=10)
        assert stale == []


class TestRedisConnectionManager:
    def test_total_connections(self):
        mgr = RedisConnectionManager()
        assert mgr.total_connections() == 0
        mgr.active_connections["group1"] = {MagicMock(), MagicMock()}
        assert mgr.total_connections() == 2

    def test_disconnect_removes_from_group(self):
        mgr = RedisConnectionManager()
        ws = MagicMock()
        mgr.active_connections["g1"] = {ws}
        mgr.disconnect(ws, "g1")
        assert "g1" not in mgr.active_connections

    def test_disconnect_empty_group_removed(self):
        mgr = RedisConnectionManager()
        ws = MagicMock()
        mgr.active_connections["g1"] = set()
        mgr.disconnect(ws, "g1")
        assert "g1" not in mgr.active_connections

    def test_start_cleanup(self):
        mgr = RedisConnectionManager()
        mock_task = MagicMock()
        mock_task.done.return_value = False
        with patch("asyncio.create_task", return_value=mock_task):
            mgr.start_cleanup()
        assert mgr.cleanup_task is not None

    def test_start_cleanup_idempotent(self):
        mgr = RedisConnectionManager()
        mock_task = MagicMock()
        mock_task.done.return_value = False
        with patch("asyncio.create_task", return_value=mock_task):
            mgr.start_cleanup()
            task1 = mgr.cleanup_task
            mgr.start_cleanup()
            assert mgr.cleanup_task is task1

    def test_stop_cleanup(self):
        mgr = RedisConnectionManager()
        mock_task = MagicMock()
        mock_task.done.return_value = False
        with patch("asyncio.create_task", return_value=mock_task):
            mgr.start_cleanup()
            mgr.stop_cleanup()
        mock_task.cancel.assert_called_once()

    def test_set_redis(self):
        mgr = RedisConnectionManager()
        mock_redis = MagicMock()
        mgr.set_redis(mock_redis)
        assert mgr.redis is mock_redis

    @pytest.mark.asyncio
    async def test_broadcast_with_redis(self):
        mgr = RedisConnectionManager()
        mock_redis = AsyncMock()
        mgr.set_redis(mock_redis)
        await mgr.broadcast({"lat": 13.0}, "group1")
        mock_redis.publish.assert_called_once_with("tracking:group1", ANY)

    @pytest.mark.asyncio
    async def test_broadcast_without_redis(self):
        mgr = RedisConnectionManager()
        ws = AsyncMock()
        mgr.active_connections["g1"] = {ws}
        await mgr.broadcast({"lat": 13.0}, "g1")
        ws.send_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_broadcast_send_error_removes_client(self):
        mgr = RedisConnectionManager()
        ws = AsyncMock()
        ws.send_text = AsyncMock(side_effect=Exception("Send failed"))
        mgr.active_connections["g1"] = {ws}
        await mgr.broadcast({"lat": 13.0}, "g1")
        assert "g1" not in mgr.active_connections
