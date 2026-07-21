# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Enterprise logging utilities for SafeVixAI Backend.

Provides structured JSON logging for production log aggregation
(Render, CloudWatch, etc.) and human-readable formatting for development.
"""

from __future__ import annotations

import json
import logging
import sys


class JsonFormatter(logging.Formatter):
    """Emit one JSON object per log line for machine-parseable log ingestion.

    Used in production environments where logs are consumed by log aggregators.
    In development, a human-readable format with colour-coded levels is used instead.
    """

    def format(self, record: logging.LogRecord) -> str:
        payload: dict = {
            "ts": self.formatTime(record, datefmt="%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        for key in ("request_id", "method", "path", "status", "duration_ms"):
            if hasattr(record, key):
                payload[key] = getattr(record, key)
        return json.dumps(payload, ensure_ascii=False)


def configure_logging(environment: str, name: str = "safevixai") -> logging.Logger:
    """Configure root logger with environment-appropriate formatting.

    Args:
        environment: 'production' or 'development'
        name: Logger name to return

    Returns:
        Configured logger instance
    """
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.handlers.clear()
    handler = logging.StreamHandler(sys.stdout)
    if environment == "production":
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        )
    root.addHandler(handler)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    return logging.getLogger(name)
