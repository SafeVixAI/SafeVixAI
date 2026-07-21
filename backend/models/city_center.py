# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""City center coordinates for discover_city() fallback and offline bundles."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, String
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class CityCenter(Base):
    """Canonical city-center coordinates used for locator fallback and offline bundles."""

    __tablename__ = 'city_centers'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    city_slug: Mapped[str] = mapped_column(
        String(64), nullable=False, unique=True, index=True,
        comment='Lowercase ASCII slug — chennai, bengaluru, …',
    )
    display_name: Mapped[str] = mapped_column(
        String(128), nullable=False,
        comment='Human-readable city name — Chennai, Bengaluru, …',
    )
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lon: Mapped[float] = mapped_column(Float, nullable=False)
    is_offline_bundle: Mapped[bool] = mapped_column(
        default=False, nullable=False,
        comment='True if included in PWA offline emergency bundles',
    )
    state: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.utcnow(), nullable=False,
    )
