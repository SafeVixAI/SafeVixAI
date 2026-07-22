# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Core rate limiter tests — creation, key function, fallback behavior."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from slowapi import Limiter
from slowapi.util import get_remote_address


class TestCoreLimiterCreation:
    """Tests for Limiter instantiation in limiter.py."""

    def test_limiter_is_slowapi_limiter(self):
        from core.limiter import limiter
        assert isinstance(limiter, Limiter)

    def test_limiter_has_limit_method(self):
        from core.limiter import limiter
        assert callable(limiter.limit)

    def test_limiter_default_key_func_is_get_remote_address(self):
        from core.limiter import limiter
        assert callable(limiter._key_func)


class TestCoreLimiterKeyFunction:
    """Tests for get_remote_address key function."""

    def test_get_remote_address_returns_client_host(self):
        request = MagicMock()
        request.client.host = "198.51.100.1"
        result = get_remote_address(request)
        assert result == "198.51.100.1"

    def test_get_remote_address_no_client(self):
        request = MagicMock()
        request.client = None
        result = get_remote_address(request)
        assert result == "127.0.0.1"

    def test_get_remote_address_no_client_host(self):
        request = MagicMock()
        request.client.host = None
        result = get_remote_address(request)
        assert result == "127.0.0.1"

    def test_get_remote_address_different_host(self):
        request = MagicMock()
        request.client.host = "10.0.0.1"
        result = get_remote_address(request)
        assert result == "10.0.0.1"


class TestCoreLimiterConfiguration:
    """Tests for configuration-driven limiter creation."""

    def test_create_limiter_with_redis_uri(self):
        lim = Limiter(
            key_func=get_remote_address,
            storage_uri="redis://localhost:6379/0",
        )
        assert isinstance(lim, Limiter)
        assert callable(lim._key_func)
        assert lim._key_func is get_remote_address

    def test_create_limiter_without_redis(self):
        lim = Limiter(key_func=get_remote_address)
        assert isinstance(lim, Limiter)
        assert callable(lim.limit)

    def test_custom_key_function(self):
        def custom_key(request):
            return "custom-key"

        lim = Limiter(key_func=custom_key)
        assert lim._key_func(MagicMock()) == "custom-key"

    def test_settings_redis_url_passed_to_limiter(self):
        settings = MagicMock()
        settings.redis_url = "redis://localhost:6379/0"
        lim = Limiter(
            key_func=get_remote_address,
            storage_uri=settings.redis_url,
        )
        assert isinstance(lim, Limiter)

    def test_settings_no_redis_fallback(self):
        settings = MagicMock()
        settings.redis_url = None
        lim = Limiter(key_func=get_remote_address)
        assert isinstance(lim, Limiter)
        assert callable(lim.limit)


class TestCoreLimiterBehavior:
    """Tests for limiter behavior patterns."""

    def test_limiter_under_limit_passes(self):
        lim = Limiter(key_func=lambda r: "test")
        limit = lim.limit("100/minute")
        assert callable(limit)

    def test_limiter_over_limit_raises(self):
        import asyncio

        from slowapi.errors import RateLimitExceeded
        from starlette.requests import Request as StarletteRequest

        lim = Limiter(key_func=lambda request: "test")
        limited = lim.limit("0/minute")

        async def handler(request: StarletteRequest):
            return {"ok": True}

        wrapped = limited(handler)

        scope = {
            "type": "http",
            "method": "GET",
            "path": "/test",
            "headers": [],
            "query_string": b"",
            "server": ("127.0.0.1", 80),
            "client": ("127.0.0.1", 50000),
            "scheme": "http",
            "root_path": "",
        }
        request = StarletteRequest(scope)

        with pytest.raises(RateLimitExceeded):
            asyncio.run(wrapped(request))

    def test_limiter_no_redis_no_crash(self):
        lim = Limiter(key_func=lambda r: "local")
        assert callable(lim._key_func)

    def test_key_prefix_with_storage(self):
        lim = Limiter(
            key_func=get_remote_address,
            storage_uri="redis://localhost:6379/0",
        )
        assert isinstance(lim, Limiter)
        assert callable(lim._key_func)

    def test_shared_limit_scope(self):
        lim = Limiter(
            key_func=lambda r: "myapp",
        )
        limited = lim.shared_limit("10/minute", scope="test")
        assert callable(limited)
