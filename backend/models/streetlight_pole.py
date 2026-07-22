# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Streetlight pole asset registry.

ORM model for tracking individual streetlight poles with QR code support,
maintenance history, and operational status.
"""

from __future__ import annotations

from datetime import datetime

from geoalchemy2 import Geometry
from sqlalchemy import BigInteger, Boolean, DateTime, Float, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class StreetlightPole(Base):
    """Individual streetlight pole asset registry entry."""

    __tablename__ = "streetlight_poles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Identity
    pole_id: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    qr_code: Mapped[str | None] = mapped_column(String(100), unique=True, index=True)
    osm_node_id: Mapped[int | None] = mapped_column(BigInteger, index=True)

    # Location
    location: Mapped[object | None] = mapped_column(
        Geometry("POINT", srid=4326, spatial_index=True), nullable=True
    )
    city: Mapped[str | None] = mapped_column(String(100), index=True)
    ward_id: Mapped[str | None] = mapped_column(String(50), index=True)
    zone_name: Mapped[str | None] = mapped_column(String(100))
    street_name: Mapped[str | None] = mapped_column(String(255))

    # Technical specifications
    pole_type: Mapped[str | None] = mapped_column(String(50))
    height_meters: Mapped[float | None] = mapped_column(Float)
    lamp_type: Mapped[str | None] = mapped_column(String(50))
    wattage: Mapped[int | None] = mapped_column(Integer)
    circuit_number: Mapped[str | None] = mapped_column(String(50))
    feeder_name: Mapped[str | None] = mapped_column(String(100))

    # Operational status
    is_operational: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    last_maintenance: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    next_maintenance_due: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    installation_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    failure_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    last_failure_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Ownership
    authority: Mapped[str | None] = mapped_column(String(100))
    contractor: Mapped[str | None] = mapped_column(String(200))
    warranty_expiry: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Metadata
    photo_url: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    tags_json: Mapped[dict | None] = mapped_column(JSONB)
    maintenance_history: Mapped[list | None] = mapped_column(JSONB)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<StreetlightPole {self.pole_id} [{self.city}]>"
