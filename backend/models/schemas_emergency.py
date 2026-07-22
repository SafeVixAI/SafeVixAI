# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Emergency / SOS locator Pydantic schemas."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

EmergencyCategory = Literal['hospital', 'police', 'ambulance', 'fire', 'towing', 'pharmacy', 'puncture', 'showroom']


class EmergencyNumber(BaseModel):
    name: str = Field(description="Service name")
    number: str = Field(description="Phone number")
    category: str | None = Field(None, description="Service category")


class EmergencyNumbersResponse(BaseModel):
    numbers: list[EmergencyNumber] = Field(description="List of emergency contact numbers")


class EmergencyServiceItem(BaseModel):
    id: str = Field(description="Unique service identifier")
    name: str = Field(description="Service name (e.g., Apollo Hospital)")
    type: EmergencyCategory | str = Field(description="Service type category")
    phone: str | None = Field(None, description="Contact phone number")
    lat: float = Field(description="Latitude")
    lon: float = Field(description="Longitude")
    distance_km: float | None = Field(None, description="Distance from query point in km")
    address: str | None = Field(None, description="Street address")
    is_open_now: bool | None = Field(None, description="Whether the service is currently open")
    wheelchair: bool | None = Field(None, description="Wheelchair accessibility")


class EmergencyResponse(BaseModel):
    services: list[EmergencyServiceItem] = Field(description="List of nearby services")
    count: int = Field(description="Number of services returned")
    radius_used: int = Field(description="Search radius used in meters")


class SosResponse(BaseModel):
    session_id: str = Field(description="Unique SOS session identifier")
    emergency_contacts: list[dict] = Field(default_factory=list, description="Emergency contacts notified")
    tracking_active: bool = Field(description="Whether live tracking is active")
    whatsapp_share_url: str | None = Field(None, description="WhatsApp share link")
    whatsapp_share_sms_body: str | None = Field(None, description="WhatsApp SMS body text")
