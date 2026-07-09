# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Structured logging with correlation IDs for SafeVixAI backend.

DEPRECATED: Logging is configured inline in main.py._configure_logging().
The correlation ID pattern is handled by _request_id_middleware.
Will be removed in v4.0.

Provides:
- Request correlation ID tracking
- Structured JSON logging
- Log context management
- Performance timing helpers

Phase 3: Production readiness layer.
"""
from __future__ import annotations

import uuid
import time
import logging
import contextvars

# Context variable for correlation ID
correlation_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("correlation_id", default="")


class CorrelationIdFilter(logging.Filter):
    """Logging filter to add correlation ID to log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.correlation_id = correlation_id_var.get() or "no-correlation-id"
        return True


class StructuredFormatter(logging.Formatter):
    """JSON structured log formatter."""

    def format(self, record: logging.LogRecord) -> str:
        import json
        
        log_data = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": getattr(record, "correlation_id", "no-correlation-id"),
        }
        
        # Add exception info if present
        if record.exc_info and record.exc_info[0] is not None:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields
        for key in ["request_id", "user_id", "duration_ms", "status_code"]:
            value = getattr(record, key, None)
            if value is not None:
                log_data[key] = value
        
        return json.dumps(log_data)


def generate_correlation_id() -> str:
    """Generate a new correlation ID."""
    return str(uuid.uuid4())[:8]


def get_correlation_id() -> str:
    """Get current correlation ID."""
    return correlation_id_var.get()


def set_correlation_id(correlation_id: str) -> None:
    """Set correlation ID for current context."""
    correlation_id_var.set(correlation_id)


class TimingContext:
    """Context manager for timing operations."""

    def __init__(self, logger: logging.Logger, message: str, level: int = logging.DEBUG):
        self.logger = logger
        self.message = message
        self.level = level
        self.start_time: float | None = None
        self.duration_ms: float = 0.0

    def __enter__(self) -> "TimingContext":
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self.start_time is not None:
            self.duration_ms = (time.perf_counter() - self.start_time) * 1000
            self.logger.log(
                self.level,
                f"{self.message} completed in {self.duration_ms:.2f}ms",
                extra={"duration_ms": round(self.duration_ms, 2)},
            )


def setup_structured_logging(
    level: int = logging.INFO,
    json_format: bool = True,
) -> None:
    """Setup structured logging for the application.
    
    Args:
        level: Logging level
        json_format: Use JSON format (True) or text format (False)
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create handler
    handler = logging.StreamHandler()
    handler.setLevel(level)
    
    # Add correlation ID filter
    correlation_filter = CorrelationIdFilter()
    handler.addFilter(correlation_filter)
    
    # Set formatter
    if json_format:
        formatter = StructuredFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s [%(correlation_id)s] %(levelname)s %(name)s: %(message)s"
        )
    
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
    
    # Set third-party loggers to WARNING
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger with correlation ID support.
    
    Args:
        name: Logger name
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Ensure correlation ID filter is added
    if not any(isinstance(f, CorrelationIdFilter) for f in logger.filters):
        logger.addFilter(CorrelationIdFilter())
    
    return logger
