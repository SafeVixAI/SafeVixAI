# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Chat / AI provider Pydantic schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(description="User message text")
    session_id: str | None = Field(None, description="Conversation session ID")
    lat: float | None = Field(None, description="User's latitude for location-aware responses")
    lon: float | None = Field(None, description="User's longitude for location-aware responses")
    language: str | None = Field(None, description="Preferred response language code")
    user_id: str | None = Field(None, description="Authenticated user ID")
    provider_hint: str | None = Field(None, description="Preferred LLM provider hint")
    provider_model: str | None = Field(None, description="Preferred model name")


class ChatResponse(BaseModel):
    reply: str = Field(description="AI response text")
    session_id: str | None = Field(None, description="Session ID for continuation")
    sources: list[dict] = Field(default_factory=list, description="RAG source references")
    intent: str | None = Field(None, description="Detected intent classification")
    safety_check: str | None = Field(None, description="Safety check result")
    provider: str | None = Field(None, description="Provider used for this response")
    model: str | None = Field(None, description="Model used for this response")
