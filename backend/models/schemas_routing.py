# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Routing / navigation Pydantic schemas."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


RouteProfile = Literal['driving-car', 'cycling-regular', 'foot-walking']


class RoutePoint(BaseModel):
    lat: float = Field(description="Latitude")
    lon: float = Field(description="Longitude")


class RouteBounds(BaseModel):
    min_lat: float = Field(description="Minimum latitude")
    min_lon: float = Field(description="Minimum longitude")
    max_lat: float = Field(description="Maximum latitude")
    max_lon: float = Field(description="Maximum longitude")


class RouteInstruction(BaseModel):
    text: str = Field(description="Instruction text")
    distance_meters: float = Field(0, description="Distance for this step in meters")
    duration_seconds: float = Field(0, description="Duration for this step in seconds")
    direction: str | None = Field(None, description="Turn direction")
    street_name: str | None = Field(None, description="Street name")


class RouteOption(BaseModel):
    id: str = Field(description="Route option identifier")
    summary: str = Field(description="Short summary (e.g., Via Anna Salai)")
    distance_meters: float = Field(description="Total distance in meters")
    duration_seconds: float = Field(description="Total duration in seconds")
    polyline: str | None = Field(None, description="Encoded polyline geometry")
    bounds: RouteBounds | None = Field(None, description="Route bounding box")
    instructions: list[dict] = Field(default_factory=list, description="Turn-by-turn instructions")


class RoutePreviewResponse(BaseModel):
    provider: str
    profile: RouteProfile
    distance_meters: float
    duration_seconds: float
    path: list[RoutePoint]
    bounds: RouteBounds
    origin: RoutePoint
    destination: RoutePoint
    steps: list[RouteInstruction] = Field(default_factory=list)
    routes: list[RouteOption] = Field(default_factory=list)
    selected_route_id: str
    reroute_threshold_meters: float = 75.0
    warnings: list[str] = Field(default_factory=list)


class RouteWaypoint(BaseModel):
    lat: float = Field(description="Waypoint latitude")
    lon: float = Field(description="Waypoint longitude")
    label: str | None = Field(None, description="Optional waypoint label")
