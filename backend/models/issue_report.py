# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from geoalchemy2 import Geometry
from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class IssueReport(Base):
    __tablename__ = 'issue_reports'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    org_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    uuid: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4)

    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    tracking_number: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)

    issue_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(16), nullable=False, default='medium')
    priority: Mapped[str] = mapped_column(String(16), nullable=False, default='normal')
    status: Mapped[str] = mapped_column(String(24), nullable=False, default='new', index=True)

    title: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    steps_to_reproduce: Mapped[str | None] = mapped_column(Text, nullable=True)
    expected_behavior: Mapped[str | None] = mapped_column(Text, nullable=True)
    actual_behavior: Mapped[str | None] = mapped_column(Text, nullable=True)

    environment: Mapped[str | None] = mapped_column(Text, nullable=True)
    browser_info: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    device_info: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    os_info: Mapped[str | None] = mapped_column(String(128), nullable=True)
    app_version: Mapped[str | None] = mapped_column(String(32), nullable=True)

    attachments: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    screenshot_urls: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    screen_recording_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    logs: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    system_info: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    labels: Mapped[list | None] = mapped_column(JSONB, nullable=True, default=list)
    assignee: Mapped[str | None] = mapped_column(String(128), nullable=True)
    milestone: Mapped[str | None] = mapped_column(String(128), nullable=True)
    github_issue_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    github_issue_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    github_discussion_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    duplicate_of: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    duplicate_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_spam: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    spam_reason: Mapped[str | None] = mapped_column(String(128), nullable=True)

    ai_category: Mapped[str | None] = mapped_column(String(64), nullable=True)
    ai_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_suggested_fix: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    is_anonymous: Mapped[bool] = mapped_column(Boolean, default=False)
    reporter_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    reporter_email: Mapped[str | None] = mapped_column(String(256), nullable=True)
    location: Mapped[str | None] = mapped_column(
        Geometry(geometry_type='POINT', srid=4326, spatial_index=True),
        nullable=True,
    )

    sla_response_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sla_resolution_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC),
    )
