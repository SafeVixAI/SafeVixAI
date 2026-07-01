# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    session_id: str | None = Field(default=None, min_length=1, max_length=128)
    lat: float | None = Field(default=None, ge=-90, le=90)
    lon: float | None = Field(default=None, ge=-180, le=180)
    client_ip: str | None = Field(default=None)
    provider_hint: str | None = Field(default=None, max_length=64)
    provider_model: str | None = Field(default=None, max_length=128)
    user_id: str | None = Field(default=None, max_length=128)


class ChatResponse(BaseModel):
    response: str
    intent: str | None = None
    sources: list[str] = Field(default_factory=list)
    session_id: str


@dataclass(slots=True)
class RetrievedContext:
    source: str
    title: str
    snippet: str
    score: float
    category: str | None = None


@dataclass(slots=True)
class ToolContext:
    name: str
    summary: str
    payload: Any = None
    sources: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ConversationContext:
    session_id: str
    message: str
    intent: str
    lat: float | None = None
    lon: float | None = None
    client_ip: str | None = None
    history: list[dict[str, Any]] = field(default_factory=list)
    retrieved: list[RetrievedContext] = field(default_factory=list)
    tools: list[ToolContext] = field(default_factory=list)
