# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

import json

import pytest

from api.v1.tracking import (
    RedisConnectionManager,
    _is_valid_location,
    _is_valid_tracking_payload,
    _is_valid_ws_token,
    _origin_allowed,
)


class TestLocationValidation:
    def test_valid_lat_lon(self):
        assert _is_valid_location(13.0827, minimum=-90, maximum=90) is True
        assert _is_valid_location(80.2707, minimum=-180, maximum=180) is True

    def test_invalid_lat(self):
        assert _is_valid_location(91.0, minimum=-90, maximum=90) is False
        assert _is_valid_location(-91.0, minimum=-90, maximum=90) is False

    def test_invalid_lon(self):
        assert _is_valid_location(181.0, minimum=-180, maximum=180) is False
        assert _is_valid_location(-181.0, minimum=-180, maximum=180) is False

    def test_none_is_valid(self):
        assert _is_valid_location(None, minimum=-90, maximum=90) is True

    def test_string_is_invalid(self):
        assert _is_valid_location("abc", minimum=-90, maximum=90) is False


class TestPayloadValidation:
    def test_valid_payload(self):
        assert _is_valid_tracking_payload({"lat": 13.0827, "lon": 80.2707}) is True

    def test_valid_payload_alternate_keys(self):
        assert _is_valid_tracking_payload({"latitude": 13.0827, "longitude": 80.2707}) is True

    def test_invalid_payload_missing_coords(self):
        assert _is_valid_tracking_payload({}) is False

    def test_invalid_payload_not_dict(self):
        assert _is_valid_tracking_payload("not a dict") is False

    def test_invalid_payload_bad_lat(self):
        assert _is_valid_tracking_payload({"lat": "invalid", "lon": 80.2707}) is False


class TestOriginValidation:
    def test_wildcard_allows_in_dev(self, monkeypatch):
        monkeypatch.setenv("CORS_ORIGINS", "*")
        monkeypatch.setenv("ENVIRONMENT", "development")
        from core.config import get_settings
        get_settings.cache_clear()
        try:
            assert _origin_allowed("http://localhost:3000") is True
        finally:
            get_settings.cache_clear()

    def test_specific_origin_allowed(self, monkeypatch):
        monkeypatch.setenv("CORS_ORIGINS", "http://localhost:3000,https://safevixai.vercel.app")
        monkeypatch.setenv("ENVIRONMENT", "production")
        from core.config import get_settings
        get_settings.cache_clear()
        try:
            assert _origin_allowed("http://localhost:3000") is True
        finally:
            get_settings.cache_clear()


class TestWebSocketTokenValidation:
    def test_none_token_rejected(self):
        assert _is_valid_ws_token(None) is False

    def test_empty_token_rejected(self):
        assert _is_valid_ws_token("") is False

    def test_invalid_token_rejected(self):
        assert _is_valid_ws_token("not-a-valid-jwt") is False


class TestRedisConnectionManager:
    @pytest.fixture
    def manager(self):
        return RedisConnectionManager()

    def test_connect_adds_connection(self, manager):
        class FakeWebSocket:
            async def accept(self):
                pass

            async def send_text(self, data):
                pass

        ws = FakeWebSocket()
        import asyncio

        async def test():
            await manager.connect(ws, "test-group")
            assert "test-group" in manager.active_connections
            assert ws in manager.active_connections["test-group"]
            manager.disconnect(ws, "test-group")

        asyncio.run(test())

    def test_disconnect_removes_connection(self, manager):
        class FakeWebSocket:
            async def accept(self):
                pass

            async def send_text(self, data):
                pass

        ws = FakeWebSocket()
        import asyncio

        async def test():
            await manager.connect(ws, "test-group")
            manager.disconnect(ws, "test-group")
            assert "test-group" not in manager.active_connections

        asyncio.run(test())

    def test_local_broadcast(self, manager):
        class FakeWebSocket:
            def __init__(self):
                self.messages = []

            async def accept(self):
                pass

            async def send_text(self, data):
                self.messages.append(data)

        ws1 = FakeWebSocket()
        ws2 = FakeWebSocket()
        import asyncio

        async def test():
            await manager.connect(ws1, "broadcast-group")
            await manager.connect(ws2, "broadcast-group")
            await manager._local_broadcast({"type": "location", "lat": 13.08}, "broadcast-group")
            assert len(ws1.messages) == 1
            assert len(ws2.messages) == 1
            assert json.loads(ws1.messages[0])["lat"] == 13.08
            manager.disconnect(ws1, "broadcast-group")
            manager.disconnect(ws2, "broadcast-group")

        asyncio.run(test())

    def test_broadcast_without_redis(self, manager):
        class FakeWebSocket:
            def __init__(self):
                self.messages = []

            async def accept(self):
                pass

            async def send_text(self, data):
                self.messages.append(data)

        ws = FakeWebSocket()
        import asyncio

        async def test():
            await manager.connect(ws, "no-redis-group")
            await manager.broadcast({"type": "test"}, "no-redis-group")
            assert len(ws.messages) == 1
            manager.disconnect(ws, "no-redis-group")

        asyncio.run(test())
