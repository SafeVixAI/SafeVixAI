# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

import asyncio
from unittest.mock import MagicMock, patch

import pytest

from core.service_tracing import (
    trace_chatbot_request,
    trace_emergency_lookup,
    trace_operation,
    trace_sos_dispatch,
    traced,
)


@pytest.fixture(autouse=True)
def reset_tracer():
    with patch("core.service_tracing._tracer") as mock_tracer:
        mock_tracer.start_span.return_value = MagicMock()
        mock_tracer.start_as_current_span.return_value.__enter__.return_value = MagicMock()
        yield mock_tracer


class TestTraceOperation:
    def test_context_manager_basic(self, reset_tracer):
        mock_tracer = reset_tracer
        with trace_operation("test-op") as span:
            span.set_attribute("key", "value")
        mock_tracer.start_as_current_span.assert_called_once_with("test-op")
        span.set_attribute.assert_any_call("service", "safevixai")
        span.set_attribute.assert_any_call("key", "value")

    def test_with_custom_service(self, reset_tracer):
        with trace_operation("custom-op", service="my-service") as span:
            pass
        span.set_attribute.assert_any_call("service", "my-service")

    def test_with_attributes(self, reset_tracer):
        attrs = {"user_id": "123", "action": "login"}
        with trace_operation("attr-op", attributes=attrs) as span:
            pass
        span.set_attribute.assert_any_call("user_id", "123")
        span.set_attribute.assert_any_call("action", "login")

    def test_span_yielded(self, reset_tracer):
        mock_tracer = reset_tracer
        mock_span = MagicMock()
        mock_tracer.start_as_current_span.return_value.__enter__.return_value = mock_span
        with trace_operation("yield-test") as span:
            assert span is mock_span

    def test_empty_attributes(self, reset_tracer):
        with trace_operation("no-attrs", attributes=None) as span:
            pass
        assert span.set_attribute.call_count >= 1


class TestTracedDecorator:
    def test_sync_function(self, reset_tracer):
        mock_tracer = reset_tracer

        @traced()
        def my_func(a, b):
            return a + b

        result = my_func(1, 2)
        assert result == 3
        mock_tracer.start_as_current_span.assert_called_once()

    def test_sync_function_custom_name(self, reset_tracer):
        mock_tracer = reset_tracer

        @traced(name="custom-name")
        def my_func():
            return "ok"

        result = my_func()
        assert result == "ok"
        mock_tracer.start_as_current_span.assert_called_once_with("custom-name")

    def test_sync_function_failure(self, reset_tracer):

        @traced()
        def failing_func():
            raise ValueError("boom")

        with pytest.raises(ValueError, match="boom"):
            failing_func()

    def test_async_function(self, reset_tracer):
        mock_tracer = reset_tracer

        @traced()
        async def async_func(x):
            return x * 2

        result = asyncio.run(async_func(5))
        assert result == 10
        mock_tracer.start_as_current_span.assert_called_once()

    def test_async_function_failure(self, reset_tracer):

        @traced()
        async def failing_async():
            raise RuntimeError("async boom")

        with pytest.raises(RuntimeError, match="async boom"):
            asyncio.run(failing_async())

    def test_sets_success_true(self, reset_tracer):
        mock_tracer = reset_tracer
        mock_span = mock_tracer.start_as_current_span.return_value.__enter__.return_value

        @traced()
        def ok_func():
            return 42

        ok_func()
        mock_span.set_attribute.assert_any_call("success", True)

    def test_includes_function_attribute(self, reset_tracer):
        mock_tracer = reset_tracer
        mock_span = mock_tracer.start_as_current_span.return_value.__enter__.return_value

        @traced()
        def sample():
            pass

        sample()
        calls = [c.args for c in mock_span.set_attribute.call_args_list]
        assert any(k == "function" for k, _ in calls)

    def test_default_name_from_module(self, reset_tracer):
        mock_tracer = reset_tracer

        @traced()
        def some_func():
            pass

        some_func()
        name = mock_tracer.start_as_current_span.call_args[0][0]
        assert "some_func" in name


class TestTraceHelpers:
    def test_trace_sos_dispatch(self, reset_tracer):
        mock_tracer = reset_tracer
        mock_span = MagicMock()
        mock_tracer.start_span.return_value = mock_span

        result = trace_sos_dispatch(13.0827, 80.2707, True)

        assert result is mock_span
        mock_tracer.start_span.assert_called_once_with("sos.dispatch")
        mock_span.set_attribute.assert_any_call("sos.latitude", 13.0827)
        mock_span.set_attribute.assert_any_call("sos.longitude", 80.2707)
        mock_span.set_attribute.assert_any_call("sos.is_online", True)

    def test_trace_emergency_lookup(self, reset_tracer):
        mock_tracer = reset_tracer
        mock_span = MagicMock()
        mock_tracer.start_span.return_value = mock_span

        result = trace_emergency_lookup("hospital", 12.97, 77.59, 5000)

        assert result is mock_span
        mock_tracer.start_span.assert_called_once_with("emergency.lookup")
        mock_span.set_attribute.assert_any_call("emergency.service_type", "hospital")
        mock_span.set_attribute.assert_any_call("emergency.latitude", 12.97)
        mock_span.set_attribute.assert_any_call("emergency.longitude", 77.59)
        mock_span.set_attribute.assert_any_call("emergency.radius_meters", 5000)

    def test_trace_chatbot_request(self, reset_tracer):
        mock_tracer = reset_tracer
        mock_span = MagicMock()
        mock_tracer.start_span.return_value = mock_span

        result = trace_chatbot_request("legal", "en", "groq")

        assert result is mock_span
        mock_tracer.start_span.assert_called_once_with("chatbot.request")
        mock_span.set_attribute.assert_any_call("chatbot.intent", "legal")
        mock_span.set_attribute.assert_any_call("chatbot.language", "en")
        mock_span.set_attribute.assert_any_call("chatbot.provider", "groq")

    def test_trace_helpers_return_span(self, reset_tracer):
        mock_tracer = reset_tracer
        mock_span = MagicMock()
        mock_tracer.start_span.return_value = mock_span

        sos_span = trace_sos_dispatch(0, 0, False)
        em_span = trace_emergency_lookup("police", 0, 0, 100)
        chat_span = trace_chatbot_request("general", "hi", "template")

        assert sos_span is mock_span
        assert em_span is mock_span
        assert chat_span is mock_span
