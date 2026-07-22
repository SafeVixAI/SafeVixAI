# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

from datetime import datetime

from geoalchemy2 import Geometry
from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class Ward(Base):
    __tablename__ = 'wards'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    org_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    ward_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    ward_name: Mapped[str] = mapped_column(Text, nullable=False)
    zone_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    city: Mapped[str | None] = mapped_column(Text, nullable=True)
    state_code: Mapped[str | None] = mapped_column(String(2), nullable=True)
    boundary: Mapped[str] = mapped_column(
        Geometry(geometry_type='POLYGON', srid=4326, spatial_index=True),
        nullable=False
    )
    officer_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    population: Mapped[int | None] = mapped_column(Integer, nullable=True)
    area_sqkm: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
