# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Tests for core/tracing.py — OpenTelemetry distributed tracing setup.

Uses lazy imports and pytest.importorskip to handle missing dependencies
gracefully (e.g., pkg_resources on Python 3.14+).
"""

from __future__ import annotations

import os
import sys
from unittest.mock import MagicMock, patch

import pytest

# ── OTLP Tests (mock-based, no real deps needed) ───────────────────────────

def _make_otel_mock_modules():
    """Create mock opentelemetry modules in sys.modules so core.tracing can be
    imported without requiring the real opentelemetry packages."""
    # We need: opentelemetry, opentelemetry.instrumentation.fastapi,
    # opentelemetry.sdk.resources, opentelemetry.sdk.trace,
    # opentelemetry.sdk.trace.export
    # Also pkg_resources which is needed by opentelemetry.instrumentation.dependencies
    fastapi_instrumentor = MagicMock()
    resource = MagicMock()
    tracer_provider = MagicMock()
    batch_span_processor = MagicMock()
    console_exporter = MagicMock()

    # opentelemetry.trace
    otel_trace = MagicMock()
    otel_trace.Tracer = MagicMock()
    otel_trace.get_tracer = MagicMock(return_value=MagicMock())
    otel_trace.set_tracer_provider = MagicMock()

    opentelemetry = MagicMock()
    opentelemetry.trace = otel_trace

    # opentelemetry.instrumentation.fastapi
    otel_instrumentation = MagicMock()
    otel_instrumentation.fastapi = MagicMock()

    # opentelemetry.instrumentation - use a real module stub
    # so that sub-module lookups work correctly
    otel_inst_module = MagicMock()
    otel_inst_module.fastapi = otel_instrumentation

    # opentelemetry.sdk
    otel_sdk = MagicMock()
    otel_sdk.resources = MagicMock()
    otel_sdk.resources.Resource = resource

    # opentelemetry.sdk.trace
    otel_sdk_trace = MagicMock()
    otel_sdk_trace.TracerProvider = tracer_provider

    # opentelemetry.sdk.trace.export
    otel_sdk_export = MagicMock()
    otel_sdk_export.BatchSpanProcessor = batch_span_processor
    otel_sdk_export.ConsoleSpanExporter = console_exporter
    otel_sdk_trace.export = otel_sdk_export

    mocks = {
        "pkg_resources": MagicMock(),
        "opentelemetry": opentelemetry,
        "opentelemetry.trace": otel_trace,
        "opentelemetry.instrumentation": otel_inst_module,
        "opentelemetry.instrumentation.fastapi": otel_instrumentation,
        "opentelemetry.sdk": otel_sdk,
        "opentelemetry.sdk.resources": otel_sdk.resources,
        "opentelemetry.sdk.trace": otel_sdk_trace,
        "opentelemetry.sdk.trace.export": otel_sdk_export,
    }
    return mocks


class TestTracingOTLP:
    """Tests for OTLP exporter branch in setup_tracing.

    Uses mock opentelemetry modules in sys.modules to import core.tracing
    without requiring the real opentelemetry packages to be installed.
    """

    def _import_tracing_mocked(self):
        """Import core.tracing with mocked opentelemetry dependencies.

        Deletions are done INSIDE the patch.dict context so they are
        properly scoped and restored on exit.
        """
        if "core.tracing" in sys.modules:
            del sys.modules["core.tracing"]
        with patch.dict(sys.modules, _make_otel_mock_modules(), clear=False):
            # Clear otel modules inside the patch context so deletions
            # are properly restored when the context exits
            for mod in list(sys.modules.keys()):
                if mod.startswith("opentelemetry") and "mock" not in type(sys.modules[mod]).__name__:
                    del sys.modules[mod]
            import core.tracing as ct
            return ct

    def test_setup_tracing_with_otlp_endpoint_mocked(self):
        """OTLP exporter should be added when OTEL_EXPORTER_OTLP_ENDPOINT is set."""
        with patch.dict(os.environ, {"OTEL_EXPORTER_OTLP_ENDPOINT": "http://jaeger:4317"}):
            ct = self._import_tracing_mocked()
            with patch.object(ct, "BatchSpanProcessor"), \
                 patch.object(ct, "FastAPIInstrumentor"), \
                 patch("opentelemetry.exporter.otlp.proto.grpc.trace_exporter.OTLPSpanExporter", create=True) as mock_otlp:
                mock_app = MagicMock()
                ct.setup_tracing(mock_app)
                mock_otlp.assert_called_once_with(endpoint="http://jaeger:4317")

    def test_setup_tracing_without_otlp(self):
        """Without OTEL_EXPORTER_OTLP_ENDPOINT, OTLP exporter should not be used."""
        with patch.dict(os.environ, {}, clear=True):
            ct = self._import_tracing_mocked()
            with patch.object(ct, "BatchSpanProcessor"), \
                 patch.object(ct, "FastAPIInstrumentor"):
                mock_app = MagicMock()
                provider = ct.setup_tracing(mock_app)
                assert provider is not None


# Check if OpenTelemetry SDK is installed for the remaining tests
_has_otel = False
try:
    from opentelemetry import trace as otel_trace  # noqa: F401
    from opentelemetry.sdk.trace import TracerProvider  # noqa: F401
    _has_otel = True
except ImportError:
    pass


def _import_tracing():
    """Lazy import core.tracing, skipping if dependencies missing."""
    pytest.importorskip("opentelemetry.instrumentation.fastapi",
                        reason="opentelemetry-instrumentation-fastapi not available")
    import core.tracing as ct
    return ct


@pytest.mark.skipif(not _has_otel, reason="OpenTelemetry SDK not installed")
class TestTracingConstants:
    """Tests for tracing module constants."""

    def test_service_name(self):
        ct = _import_tracing()
        assert ct.SERVICE_NAME == "safevixai-backend"

    def test_service_version_default(self):
        ct = _import_tracing()
        with patch.dict(os.environ, {}, clear=True):
            import importlib
            importlib.reload(ct)
            assert ct.SERVICE_VERSION == "dev"

    def test_service_version_from_env(self):
        ct = _import_tracing()
        with patch.dict(os.environ, {"APP_VERSION": "1.2.3"}):
            import importlib
            importlib.reload(ct)
            assert ct.SERVICE_VERSION == "1.2.3"


@pytest.mark.skipif(not _has_otel, reason="OpenTelemetry SDK not installed")
class TestSetupTracing:
    """Tests for setup_tracing function — uses mocks for external deps."""

    def test_setup_tracing_creates_provider(self):
        ct = _import_tracing()
        mock_app = MagicMock()
        with patch.object(ct, "FastAPIInstrumentor"):
            provider = ct.setup_tracing(mock_app)
            assert isinstance(provider, TracerProvider)

    def test_setup_tracing_instruments_app(self):
        ct = _import_tracing()
        mock_app = MagicMock()
        mock_fastapi = MagicMock()
        with patch.object(ct, "FastAPIInstrumentor", mock_fastapi):
            ct.setup_tracing(mock_app)
            mock_fastapi.instrument_app.assert_called_once_with(mock_app)

    def test_setup_tracing_adds_console_exporter(self):
        ct = _import_tracing()
        mock_app = MagicMock()
        with patch.object(ct, "BatchSpanProcessor") as mock_bsp, \
             patch.object(ct, "FastAPIInstrumentor"):
            ct.setup_tracing(mock_app)
            assert mock_bsp.call_count >= 1

    def test_setup_tracing_with_otlp_endpoint(self):
        ct = _import_tracing()
        with patch.dict(os.environ, {"OTEL_EXPORTER_OTLP_ENDPOINT": "http://jaeger:4317"}):
            mock_app = MagicMock()
            with patch("opentelemetry.exporter.otlp.proto.grpc.trace_exporter.OTLPSpanExporter", create=True) as mock_otlp, \
                 patch.object(ct, "BatchSpanProcessor"), \
                 patch.object(ct, "FastAPIInstrumentor"):
                ct.setup_tracing(mock_app)
                mock_otlp.assert_called_once_with(endpoint="http://jaeger:4317")

    def test_setup_tracing_sets_tracer_provider(self):
        ct = _import_tracing()
        mock_app = MagicMock()
        with patch("opentelemetry.trace.set_tracer_provider") as mock_set, \
             patch.object(ct, "BatchSpanProcessor"), \
             patch.object(ct, "FastAPIInstrumentor"):
            provider = ct.setup_tracing(mock_app)
            mock_set.assert_called_once_with(provider)


@pytest.mark.skipif(not _has_otel, reason="OpenTelemetry SDK not installed")
class TestGetTracer:
    def test_get_tracer_returns_tracer(self):
        ct = _import_tracing()
        from opentelemetry import trace as otel_trace
        tracer = ct.get_tracer()
        assert isinstance(tracer, otel_trace.Tracer)

    def test_get_tracer_with_custom_name(self):
        ct = _import_tracing()
        tracer = ct.get_tracer("custom-service")
        assert tracer is not None

    def test_get_tracer_default_name(self):
        ct = _import_tracing()
        tracer = ct.get_tracer()
        assert tracer is not None
