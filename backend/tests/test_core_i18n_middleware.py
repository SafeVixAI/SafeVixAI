# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Core i18n middleware tests — locale detection, error localization."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from core.i18n_middleware import (
    DEFAULT_LOCALE,
    SUPPORTED_LOCALES,
    get_locale_from_request,
    i18n_middleware,
    localized_http_exception_handler,
    localized_rate_limit_exceeded_handler,
    localized_validation_exception_handler,
    setup_backend_i18n,
)


class TestGetLocaleFromRequest:
    """Tests for locale extraction from cookies and headers."""

    def test_cookie_locale(self):
        request = MagicMock(spec=Request)
        request.cookies = {"svai-locale": "hi"}
        request.headers = {}
        assert get_locale_from_request(request) == "hi"

    def test_accept_language_header(self):
        request = MagicMock(spec=Request)
        request.cookies = {}
        request.headers = {"accept-language": "ta-IN, en;q=0.9"}
        assert get_locale_from_request(request) == "ta"

    def test_header_with_quality(self):
        request = MagicMock(spec=Request)
        request.cookies = {}
        request.headers = {"accept-language": "fr-CH, fr;q=0.9, en;q=0.8"}
        assert get_locale_from_request(request) == "fr"

    def test_chinese_locale_zh(self):
        request = MagicMock(spec=Request)
        request.cookies = {}
        request.headers = {"accept-language": "zh-CN,zh;q=0.9"}
        # 'zh' is not in SUPPORTED_LOCALES, should fall back to 'en'
        assert get_locale_from_request(request) == DEFAULT_LOCALE

    def test_invalid_locale_falls_back(self):
        request = MagicMock(spec=Request)
        request.cookies = {"svai-locale": "xx"}
        request.headers = {}
        assert get_locale_from_request(request) == "en"

    def test_no_cookie_no_header_falls_back(self):
        request = MagicMock(spec=Request)
        request.cookies = {}
        request.headers = {}
        assert get_locale_from_request(request) == "en"

    def test_supported_locales_contains_14(self):
        assert len(SUPPORTED_LOCALES) == 14
        assert "en" in SUPPORTED_LOCALES
        assert "hi" in SUPPORTED_LOCALES
        assert "ta" in SUPPORTED_LOCALES

    def test_cookie_takes_priority_over_header(self):
        request = MagicMock(spec=Request)
        request.cookies = {"svai-locale": "bn"}
        request.headers = {"accept-language": "ta-IN"}
        assert get_locale_from_request(request) == "bn"


class TestI18nMiddleware:
    """Tests for the ASGI middleware function."""

    @pytest.mark.asyncio
    async def test_middleware_sets_locale(self):
        request = MagicMock(spec=Request)
        request.state = MagicMock()
        request.cookies = {"svai-locale": "ta"}
        request.headers = {}

        async def call_next(req):
            assert req.state.locale == "ta"
            return JSONResponse(content={"ok": True})

        response = await i18n_middleware(request, call_next)
        assert response is not None

    @pytest.mark.asyncio
    async def test_middleware_falls_back_to_default(self):
        request = MagicMock(spec=Request)
        request.state = MagicMock()
        request.cookies = {}
        request.headers = {}

        async def call_next(req):
            assert req.state.locale == "en"
            return JSONResponse(content={"ok": True})

        response = await i18n_middleware(request, call_next)
        assert response is not None


class TestLocalizedExceptionHandlers:
    """Tests for localized exception handlers."""

    @pytest.mark.asyncio
    async def test_http_exception_translated(self):
        request = MagicMock(spec=Request)
        request.state.locale = "hi"
        exc = HTTPException(status_code=401, detail="Invalid credentials")

        with patch("core.i18n_middleware.translate_message", return_value="अमान्य क्रेडेंशियल"):
            response = await localized_http_exception_handler(request, exc)
        assert response.status_code == 401
        assert "अमान्य" in response.body.decode()

    @pytest.mark.asyncio
    async def test_http_exception_no_translation(self):
        request = MagicMock(spec=Request)
        request.state.locale = "ta"
        exc = HTTPException(status_code=404, detail="Not found")

        response = await localized_http_exception_handler(request, exc)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_http_exception_non_string_detail(self):
        """Test http handler with non-string detail (isinstance else branch)."""
        request = MagicMock(spec=Request)
        request.state.locale = "en"
        detail_list = [{"key": "value"}]
        exc = HTTPException(status_code=400, detail=detail_list)

        response = await localized_http_exception_handler(request, exc)
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_validation_exception_field_required(self):
        request = MagicMock(spec=Request)
        request.state.locale = "hi"
        exc = RequestValidationError(errors=[{"loc": ("body", "name"), "msg": "field required", "type": "value_error.missing"}])

        response = await localized_validation_exception_handler(request, exc)
        assert response.status_code == 422
        body = response.body.decode()
        assert "आवश्यक" in body

    @pytest.mark.asyncio
    async def test_validation_exception_invalid_email(self):
        request = MagicMock(spec=Request)
        request.state.locale = "ar"
        exc = RequestValidationError(errors=[{"loc": ("body", "email"), "msg": "value is not a valid email", "type": "value_error"}])

        response = await localized_validation_exception_handler(request, exc)
        assert response.status_code == 422
        body = response.body.decode()
        assert "بريد" in body

    @pytest.mark.asyncio
    async def test_validation_exception_unknown_msg_passthrough(self):
        request = MagicMock(spec=Request)
        request.state.locale = "fr"
        exc = RequestValidationError(errors=[{"loc": ("body", "x"), "msg": "some unknown error", "type": "value_error"}])

        response = await localized_validation_exception_handler(request, exc)
        assert response.status_code == 422
        body = response.body.decode()
        assert "unknown" in body


class TestRateLimitHandler:
    """Tests for rate limit exceeded handler."""

    @pytest.mark.asyncio
    async def test_rate_limit_returns_429(self):
        request = MagicMock(spec=Request)
        request.state.locale = "en"
        request.url.path = "/api/v1/test"

        fake_limit = MagicMock()
        fake_limit.error_message = None
        exc = RateLimitExceeded(fake_limit)

        response = await localized_rate_limit_exceeded_handler(request, exc)
        assert response.status_code == 429
        body = response.body.decode()
        assert "Rate limit exceeded" in body or "retry" in body.lower()

    @pytest.mark.asyncio
    async def test_rate_limit_alert_not_triggered_below_threshold(self):
        from core.i18n_middleware import _rate_limit_hits
        endpoint = "/api/v1/test-no-alert"
        _rate_limit_hits[endpoint] = []

        request = MagicMock(spec=Request)
        request.state.locale = "en"
        request.url.path = endpoint

        fake_limit = MagicMock()
        fake_limit.error_message = None
        exc = RateLimitExceeded(fake_limit)

        with patch("core.i18n_middleware.get_alert_service") as mock_alert:
            await localized_rate_limit_exceeded_handler(request, exc)
            mock_alert.return_value.alert_external_api_failed.assert_not_called()

    @pytest.mark.asyncio
    async def test_rate_limit_alert_triggers_at_threshold(self):
        """Rate limit alert should fire when hits reach threshold (lines 126-130)."""
        from core.i18n_middleware import _rate_limit_hits, _RATE_LIMIT_ALERT_THRESHOLD, _RATE_LIMIT_WINDOW_SECONDS
        import time
        endpoint = "/api/v1/test-threshold"
        now = time.time()
        # Fill up to just below threshold
        _rate_limit_hits[endpoint] = [now - 10] * (_RATE_LIMIT_ALERT_THRESHOLD - 1)

        request = MagicMock(spec=Request)
        request.state.locale = "en"
        request.url.path = endpoint

        fake_limit = MagicMock()
        fake_limit.error_message = None
        exc = RateLimitExceeded(fake_limit)

        with patch("core.i18n_middleware.get_alert_service") as mock_alert:
            await localized_rate_limit_exceeded_handler(request, exc)
            mock_alert.return_value.alert_external_api_failed.assert_called_once()

    @pytest.mark.asyncio
    async def test_setup_backend_i18n_registers_handlers(self):
        app = FastAPI()
        setup_backend_i18n(app)
        assert hasattr(app, "middleware_stack")
        assert app.exception_handlers
        assert len(app.exception_handlers) > 0

    @pytest.mark.asyncio
    async def test_http_exception_no_state_locale(self):
        request = MagicMock(spec=Request)
        request.state = MagicMock()
        del request.state.locale
        exc = HTTPException(status_code=500, detail="Internal server error")

        response = await localized_http_exception_handler(request, exc)
        assert response.status_code == 500
