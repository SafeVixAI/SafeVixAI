# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime

from geoalchemy2 import Geometry
from sqlalchemy import BigInteger, Date, DateTime, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class RoadIssue(Base):
    __tablename__ = 'road_issues'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    org_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)  # Phase 0.6: Multi-tenant isolation
    uuid: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4)
    issue_type: Mapped[str] = mapped_column(String(64), nullable=False)
    severity: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    location: Mapped[str] = mapped_column(
        Geometry(geometry_type='POINT', srid=4326, spatial_index=True),
        nullable=False,
    )
    location_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    road_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    road_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    road_number: Mapped[str | None] = mapped_column(String(64), nullable=True)
    photo_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_detection: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    reporter_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    authority_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    authority_phone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    authority_email: Mapped[str | None] = mapped_column(Text, nullable=True)
    complaint_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default='open')
    status_updated: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    # Enterprise extensions
    category: Mapped[str] = mapped_column(String(32), default='roads', index=True)
    sub_category: Mapped[str | None] = mapped_column(String(64), nullable=True)
    city: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    ward_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    ward_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    assigned_officer_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    sla_deadline: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    duplicate_of_uuid: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    citizen_phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    confirmation_count: Mapped[int] = mapped_column(Integer, default=0)
    before_photo_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    after_photo_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    ai_model_version: Mapped[str | None] = mapped_column(String(32), nullable=True)


class RoadInfrastructure(Base):
    __tablename__ = 'road_infrastructure'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    org_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)  # Phase 0.6: Multi-tenant isolation
    road_id: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    road_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    road_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    road_number: Mapped[str | None] = mapped_column(String(64), nullable=True)
    length_km: Mapped[float | None] = mapped_column(Float, nullable=True)
    geometry: Mapped[str] = mapped_column(
        Geometry(geometry_type='LINESTRING', srid=4326, spatial_index=True),
        nullable=False,
    )
    state_code: Mapped[str | None] = mapped_column(String(2), nullable=True, index=True)
    contractor_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    exec_engineer: Mapped[str | None] = mapped_column(Text, nullable=True)
    exec_engineer_phone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    budget_sanctioned: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    budget_spent: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    construction_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    last_relayed_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    next_maintenance: Mapped[date | None] = mapped_column(Date, nullable=True)
    project_source: Mapped[str | None] = mapped_column(String(64), nullable=True)
    data_source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
