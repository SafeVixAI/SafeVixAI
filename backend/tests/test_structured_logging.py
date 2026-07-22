# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Structured logging tests for SafeVixAI backend."""
from __future__ import annotations

import json
import logging
import time

from core.structured_logging import (
    CorrelationIdFilter,
    StructuredFormatter,
    TimingContext,
    correlation_id_var,
    generate_correlation_id,
    get_correlation_id,
    get_logger,
    set_correlation_id,
    setup_structured_logging,
)

# ── Correlation ID Tests ────────────────────────────────────────────────────

class TestCorrelationId:
    """Tests for correlation ID management."""

    def test_generate_correlation_id(self):
        """Test correlation ID generation."""
        cid = generate_correlation_id()
        assert len(cid) == 8
        assert isinstance(cid, str)

    def test_generate_unique_ids(self):
        """Test generated IDs are unique."""
        ids = [generate_correlation_id() for _ in range(100)]
        assert len(set(ids)) == 100

    def test_get_set_correlation_id(self):
        """Test get/set correlation ID."""
        set_correlation_id("test-123")
        assert get_correlation_id() == "test-123"

    def test_default_correlation_id(self):
        """Test default correlation ID is empty."""
        correlation_id_var.set("")
        assert get_correlation_id() == ""


# ── Correlation ID Filter Tests ─────────────────────────────────────────────

class TestCorrelationIdFilter:
    """Tests for CorrelationIdFilter."""

    def test_filter_adds_correlation_id(self):
        """Test filter adds correlation ID to record."""
        set_correlation_id("test-123")

        log_filter = CorrelationIdFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        result = log_filter.filter(record)
        assert result is True
        assert record.correlation_id == "test-123"

    def test_filter_default_correlation_id(self):
        """Test filter uses default when no correlation ID."""
        correlation_id_var.set("")

        log_filter = CorrelationIdFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        log_filter.filter(record)
        assert record.correlation_id == "no-correlation-id"


# ── Structured Formatter Tests ──────────────────────────────────────────────

class TestStructuredFormatter:
    """Tests for StructuredFormatter."""

    def test_format_json(self):
        """Test JSON formatting."""
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.correlation_id = "test-123"

        result = formatter.format(record)
        log_data = json.loads(result)

        assert log_data["level"] == "INFO"
        assert log_data["logger"] == "test.logger"
        assert log_data["message"] == "Test message"
        assert log_data["correlation_id"] == "test-123"
        assert "timestamp" in log_data

    def test_format_with_exception(self):
        """Test formatting with exception info."""
        formatter = StructuredFormatter()

        try:
            raise ValueError("Test error")
        except ValueError:
            import sys
            record = logging.LogRecord(
                name="test.logger",
                level=logging.ERROR,
                pathname="test.py",
                lineno=1,
                msg="Error occurred",
                args=(),
                exc_info=sys.exc_info(),
            )
            record.correlation_id = "test-123"

            result = formatter.format(record)
            log_data = json.loads(result)

            assert "exception" in log_data
            assert "ValueError" in log_data["exception"]

    def test_format_with_extra_fields(self):
        """Test formatting with extra fields."""
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.correlation_id = "test-123"
        record.duration_ms = 150.5
        record.status_code = 200

        result = formatter.format(record)
        log_data = json.loads(result)

        assert log_data["duration_ms"] == 150.5
        assert log_data["status_code"] == 200


# ── Timing Context Tests ────────────────────────────────────────────────────

class TestTimingContext:
    """Tests for TimingContext."""

    def test_timing_context(self):
        """Test timing context measures duration."""
        logger = logging.getLogger("test.timing")
        logger.setLevel(logging.DEBUG)

        with TimingContext(logger, "Test operation") as timing:
            time.sleep(0.1)

        assert timing.duration_ms >= 100

    def test_timing_context_logs(self, caplog):
        """Test timing context logs duration."""
        logger = logging.getLogger("test.timing")
        logger.setLevel(logging.DEBUG)
        logger.handlers.clear()
        logger.propagate = True
        with caplog.at_level(logging.DEBUG), TimingContext(logger, "Test operation"):
            time.sleep(0.05)

        assert "completed in" in caplog.text
        assert "ms" in caplog.text

    def test_timing_context_no_start_time(self):
        """__exit__ should handle missing start_time gracefully (line 90 branch)."""
        logger = logging.getLogger("test.timing")
        ctx = TimingContext(logger, "Never started")
        ctx.__exit__(None, None, None)
        assert ctx.duration_ms == 0.0


# ── Logger Setup Tests ──────────────────────────────────────────────────────

class TestLoggerSetup:
    """Tests for logger setup."""

    def test_setup_structured_logging(self):
        """Test structured logging setup with JSON format."""
        setup_structured_logging(level=logging.DEBUG, json_format=True)

        root_logger = logging.getLogger()
        assert root_logger.level == logging.DEBUG
        assert len(root_logger.handlers) > 0

    def test_setup_structured_logging_text_format(self):
        """Test structured logging setup with text (non-JSON) format."""
        setup_structured_logging(level=logging.INFO, json_format=False)

        root_logger = logging.getLogger()
        assert root_logger.level == logging.INFO
        assert len(root_logger.handlers) > 0

    def test_setup_structured_logging_sets_uvicorn_level(self):
        """setup_structured_logging should set uvicorn logger to WARNING (line 128)."""
        setup_structured_logging(level=logging.DEBUG, json_format=True)
        uvicorn_logger = logging.getLogger("uvicorn")
        assert uvicorn_logger.level == logging.WARNING

    def test_get_logger(self):
        """Test get_logger returns configured logger."""
        logger = get_logger("test.module")

        assert logger.name == "test.module"
        assert any(isinstance(f, CorrelationIdFilter) for f in logger.filters)

    def test_get_logger_with_existing_filter(self):
        """get_logger should not add duplicate filter (lines 153-156 branch)."""
        logger = get_logger("test.dedup")
        count_before = sum(1 for f in logger.filters if isinstance(f, CorrelationIdFilter))
        logger2 = get_logger("test.dedup")
        count_after = sum(1 for f in logger2.filters if isinstance(f, CorrelationIdFilter))
        # Should not add another filter if one already exists
        assert count_after == count_before


# ── Integration Tests ───────────────────────────────────────────────────────

class TestLoggingIntegration:
    """Integration tests for logging system."""

    def test_full_logging_flow(self):
        """Test full logging flow with correlation ID."""
        set_correlation_id("integration-test")
        logger = get_logger("integration.test")

        assert logger.name == "integration.test"
        assert get_correlation_id() == "integration-test"

    def test_timing_with_correlation_id(self):
        """Test timing context includes correlation ID."""
        set_correlation_id("timing-test")
        logger = get_logger("timing.test")
        logger.setLevel(logging.DEBUG)

        import io
        handler = logging.StreamHandler(io.StringIO())
        handler.setLevel(logging.DEBUG)
        handler.addFilter(CorrelationIdFilter())
        handler.setFormatter(StructuredFormatter())
        logger.addHandler(handler)

        with TimingContext(logger, "Timed operation"):
            time.sleep(0.01)

        assert get_correlation_id() == "timing-test"
        logger.removeHandler(handler)
