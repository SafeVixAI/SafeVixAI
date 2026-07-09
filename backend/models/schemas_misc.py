# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Miscellaneous Pydantic schemas — garage, telemetry, service candidate."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ServiceCandidate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    category: str
    lat: float
    lon: float
    distance_meters: float


class VehicleGarageItem(BaseModel):
    vehicle_id: str = Field(description="Vehicle identifier")
    registration_number: str = Field(description="Vehicle registration number")
    vehicle_type: str = Field(description="Vehicle type (car, bike, truck, etc.)")
    make: str | None = Field(None, description="Manufacturer")
    model: str | None = Field(None, description="Model name")
    year: int | None = Field(None, description="Manufacturing year")
    last_service_date: str | None = Field(None, description="Last service date")
    next_service_due: str | None = Field(None, description="Next service due date")


class GarageSyncResponse(BaseModel):
    synced_count: int = Field(0, description="Number of vehicles synced")
    status: str = Field(description="Sync status")
    errors: list[str] = Field(default_factory=list, description="Sync errors")


class TelemetryDataPoint(BaseModel):
    timestamp: str = Field(description="ISO 8601 timestamp")
    lat: float = Field(description="Latitude")
    lon: float = Field(description="Longitude")
    speed_kmh: float | None = Field(None, description="Speed in km/h")
    heading: float | None = Field(None, description="Heading in degrees")
    battery_level: float | None = Field(None, description="Battery level 0-100")
    accuracy_meters: float | None = Field(None, description="GPS accuracy in meters")
