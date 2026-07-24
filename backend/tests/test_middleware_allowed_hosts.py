# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Tests for middleware/allowed_hosts.py — AllowedHostsMiddleware and setup_allowed_hosts."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from urllib.parse import urlparse

import pytest

from middleware.allowed_hosts import AllowedHostsMiddleware, setup_allowed_hosts


class TestAllowedHostsMiddleware:
    @pytest.mark.asyncio
    async def test_non_http_scope_passes_through(self):
        app = AsyncMock()
        middleware = AllowedHostsMiddleware(app)
        scope = {"type": "websocket"}
        await middleware(scope, None, None)
        app.assert_awaited_once_with(scope, None, None)

    @pytest.mark.asyncio
    async def test_allowed_host_passes(self):
        app = AsyncMock()
        middleware = AllowedHostsMiddleware(app, allowed_hosts=["example.com"])

        scope = {
            "type": "http",
            "headers": [(b"host", b"example.com")],
        }
        receive = AsyncMock()
        send = AsyncMock()
        await middleware(scope, receive, send)
        app.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_blocked_host_returns_403(self):
        app = AsyncMock()
        middleware = AllowedHostsMiddleware(app, allowed_hosts=["example.com"])

        scope = {
            "type": "http",
            "headers": [(b"host", b"evil.com")],
        }
        receive = AsyncMock()
        send = AsyncMock()
        await middleware(scope, receive, send)
        # app should NOT be called
        app.assert_not_awaited()
        # send should have been called with a 403 response
        assert send.called

    @pytest.mark.asyncio
    async def test_blocked_host_returns_403_response_body(self):
        app = AsyncMock()
        middleware = AllowedHostsMiddleware(app, allowed_hosts=["safevixai.com"])

        scope = {
            "type": "http",
            "headers": [(b"host", b"malicious.com")],
        }
        receive = AsyncMock()
        send = AsyncMock()

        await middleware(scope, receive, send)

        # Check the response was sent
        send_call_args_list = send.call_args_list
        # First message should be the start, second the body
        status_code = None
        body_content = None
        for call_args in send_call_args_list:
            message = call_args[0][0]
            if message.get("type") == "http.response.start":
                status_code = message["status"]
            elif message.get("type") == "http.response.body":
                body_content = message.get("body", b"")

        assert status_code == 403
        assert body_content is not None
        assert b"Host not allowed" in body_content

    @pytest.mark.asyncio
    async def test_empty_allowed_hosts_allows_all(self):
        app = AsyncMock()
        middleware = AllowedHostsMiddleware(app, allowed_hosts=[])

        scope = {
            "type": "http",
            "headers": [(b"host", b"anything.com")],
        }
        receive = AsyncMock()
        send = AsyncMock()
        await middleware(scope, receive, send)
        app.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_none_allowed_hosts_allows_all(self):
        app = AsyncMock()
        middleware = AllowedHostsMiddleware(app, allowed_hosts=None)

        scope = {
            "type": "http",
            "headers": [(b"host", b"anything.com")],
        }
        receive = AsyncMock()
        send = AsyncMock()
        await middleware(scope, receive, send)
        app.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_host_with_port_strips_port(self):
        app = AsyncMock()
        middleware = AllowedHostsMiddleware(app, allowed_hosts=["example.com"])

        scope = {
            "type": "http",
            "headers": [(b"host", b"example.com:8080")],
        }
        receive = AsyncMock()
        send = AsyncMock()
        await middleware(scope, receive, send)
        app.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_host_case_insensitive(self):
        app = AsyncMock()
        # The middleware compares lowercased host vs allowed list
        middleware = AllowedHostsMiddleware(app, allowed_hosts=["example.com"])

        scope = {
            "type": "http",
            "headers": [(b"host", b"Example.COM")],
        }
        receive = AsyncMock()
        send = AsyncMock()
        await middleware(scope, receive, send)
        app.assert_awaited_once()


class TestSetupAllowedHosts:
    def test_production_with_frontend_url(self):
        app = MagicMock()
        settings = MagicMock()
        settings.environment = "production"
        settings.allowed_hosts_env = None
        settings.frontend_url = "https://app.safevixai.com"
        settings.chatbot_service_url = "http://chatbot:8010/api/v1"

        setup_allowed_hosts(app, settings)

        app.add_middleware.assert_called_once()
        args, kwargs = app.add_middleware.call_args
        middleware_class = args[0]
        allowed_hosts = kwargs.get("allowed_hosts", [])
        assert middleware_class == AllowedHostsMiddleware
        hosts_set = set(allowed_hosts)
        assert "app.safevixai.com" in hosts_set

    def test_production_without_frontend_url_defaults_localhost(self):
        app = MagicMock()
        settings = MagicMock()
        settings.environment = "production"
        settings.allowed_hosts_env = None
        settings.frontend_url = None
        settings.chatbot_service_url = "http://localhost:8010/api/v1"

        setup_allowed_hosts(app, settings)

        app.add_middleware.assert_called_once()
        args, kwargs = app.add_middleware.call_args
        allowed_hosts = kwargs.get("allowed_hosts", [])
        assert any(h in ("localhost", "127.0.0.1") for h in allowed_hosts)

    def test_production_multiple_urls(self):
        app = MagicMock()
        settings = MagicMock()
        settings.environment = "production"
        settings.allowed_hosts_env = None
        settings.frontend_url = "https://app.safevixai.com"
        settings.chatbot_service_url = "http://chatbot.safevixai.internal:8010/api/v1"

        setup_allowed_hosts(app, settings)

        app.add_middleware.assert_called_once()
        args, kwargs = app.add_middleware.call_args
        allowed_hosts_list = kwargs.get("allowed_hosts", [])
        parsed_frontend = urlparse(settings.frontend_url)
        parsed_chatbot = urlparse(settings.chatbot_service_url)
        hostnames = set(allowed_hosts_list)
        assert parsed_frontend.hostname in hostnames
        assert parsed_chatbot.hostname in hostnames

    def test_non_production_with_env_var(self):
        app = MagicMock()
        settings = MagicMock()
        settings.environment = "development"
        settings.allowed_hosts_env = "dev.example.com,staging.example.com"
        settings.frontend_url = None

        setup_allowed_hosts(app, settings)

        app.add_middleware.assert_called_once()
        args, kwargs = app.add_middleware.call_args
        allowed_hosts = kwargs.get("allowed_hosts", [])
        hosts_set = set(allowed_hosts)
        assert "dev.example.com" in hosts_set
        assert "staging.example.com" in hosts_set

    def test_non_production_without_env_var_skips(self):
        app = MagicMock()
        settings = MagicMock()
        settings.environment = "development"
        settings.allowed_hosts_env = None

        setup_allowed_hosts(app, settings)

        app.add_middleware.assert_not_called()

    def test_non_production_empty_env_var_skips(self):
        app = MagicMock()
        settings = MagicMock()
        settings.environment = "development"
        settings.allowed_hosts_env = ""

        setup_allowed_hosts(app, settings)

        app.add_middleware.assert_not_called()
