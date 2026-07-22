# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Custom tracing helpers for SafeVixAI backend services.

DEPRECATED: Use core.tracing.setup_tracing() and core.tracing.get_tracer() instead.
Will be removed in v4.0.
"""
from __future__ import annotations

import asyncio
import functools
from collections.abc import Callable
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, TypeVar

from opentelemetry import trace

if TYPE_CHECKING:
    from collections.abc import Generator

T = TypeVar("T")
_tracer = trace.get_tracer("safevixai-services")


@contextmanager
def trace_operation(
    name: str,
    service: str = "safevixai",
    attributes: dict[str, Any] | None = None,
) -> Generator[trace.Span, None, None]:
    """Context manager for tracing a single operation."""
    with _tracer.start_as_current_span(name) as span:
        span.set_attribute("service", service)
        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, value)
        yield span


def traced(
    name: str | None = None,
    service: str = "safevixai",
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator to trace a function or method."""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        operation_name = name or f"{func.__module__}.{func.__qualname__}"

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> T:
            with trace_operation(operation_name, service=service) as span:
                span.set_attribute("function", func.__qualname__)
                try:
                    result = await func(*args, **kwargs)
                    span.set_attribute("success", True)
                    return result
                except Exception as e:
                    span.set_attribute("success", False)
                    span.record_exception(e)
                    raise

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> T:
            with trace_operation(operation_name, service=service) as span:
                span.set_attribute("function", func.__qualname__)
                try:
                    result = func(*args, **kwargs)
                    span.set_attribute("success", True)
                    return result
                except Exception as e:
                    span.set_attribute("success", False)
                    span.record_exception(e)
                    raise

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator


# Add business-specific tracing helpers
def trace_sos_dispatch(lat: float, lon: float, is_online: bool) -> trace.Span:
    """Trace an SOS dispatch event."""
    span = _tracer.start_span("sos.dispatch")
    span.set_attribute("sos.latitude", lat)
    span.set_attribute("sos.longitude", lon)
    span.set_attribute("sos.is_online", is_online)
    return span


def trace_emergency_lookup(
    service_type: str,
    lat: float,
    lon: float,
    radius: int,
) -> trace.Span:
    """Trace an emergency service lookup."""
    span = _tracer.start_span("emergency.lookup")
    span.set_attribute("emergency.service_type", service_type)
    span.set_attribute("emergency.latitude", lat)
    span.set_attribute("emergency.longitude", lon)
    span.set_attribute("emergency.radius_meters", radius)
    return span


def trace_chatbot_request(
    intent: str,
    language: str,
    provider: str,
) -> trace.Span:
    """Trace a chatbot request."""
    span = _tracer.start_span("chatbot.request")
    span.set_attribute("chatbot.intent", intent)
    span.set_attribute("chatbot.language", language)
    span.set_attribute("chatbot.provider", provider)
    return span
