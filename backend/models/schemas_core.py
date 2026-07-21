# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Core/base Pydantic schemas — health, error, and generic API types."""

from __future__ import annotations

from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, Field


T = TypeVar("T")


class DependencyHealth(BaseModel):
    name: str = Field(description="Dependency name (e.g., database, redis)")
    healthy: bool = Field(description="Whether the dependency is healthy")
    detail: str | None = Field(None, description="Optional detail message")


class ErrorDetail(BaseModel):
    field: str | None = None
    message: str = Field(description="Error description")
    code: str | None = None


class ErrorResponse(BaseModel):
    detail: str = Field(description="Error description")
    error_code: str | None = Field(None, description="Machine-readable error code")
    status_code: int = Field(400, description="HTTP status code")
    errors: list[ErrorDetail] | None = None


class HealthResponse(BaseModel):
    status: str = Field(description="Service health status: ok | degraded | down")
    version: str = Field(description="Service version")
    timestamp: str = Field(description="ISO 8601 timestamp")
    uptime_seconds: float | None = Field(None, description="Seconds since service start")
    services: dict[str, str] | None = Field(None, description="Per-dependency health status")


class ApiResponse(BaseModel, Generic[T]):
    success: bool = Field(description="Whether the request succeeded")
    data: T | None = Field(None, description="Response payload")
    message: str | None = Field(None, description="Optional human-readable message")


class ApiErrorResponse(BaseModel):
    success: bool = False
    data: None = None
    error: dict
    timestamp: str = ""
