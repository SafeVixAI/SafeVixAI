# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Road issues / reporting Pydantic schemas."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

RoadIssueStatus = Literal['open', 'acknowledged', 'in_progress', 'resolved', 'rejected', 'pending_processing', 'verified']


class AuthorityPreviewResponse(BaseModel):
    jurisdiction: str = Field(description="Jurisdiction name")
    authority_name: str = Field(description="Authority name")
    contact: str | None = Field(None, description="Contact info")
    estimated_response_days: int | None = Field(None, description="Estimated response time in days")
    category: str | None = Field(None, description="Category of road issue")
    has_authority: bool = Field(True, description="Whether authority exists")


class RoadInfrastructureResponse(BaseModel):
    road_name: str | None = Field(None, description="Road name")
    surface_type: str | None = Field(None, description="Road surface type")
    condition: str | None = Field(None, description="Road condition assessment")
    width_meters: float | None = Field(None, description="Road width in meters")
    speed_limit_kmh: int | None = Field(None, description="Speed limit")
    maintenance_authority: str | None = Field(None, description="Responsible maintenance authority")
    last_maintenance_date: str | None = Field(None, description="Last maintenance date")


class RoadIssueItem(BaseModel):
    id: str = Field(description="Unique issue identifier")
    title: str = Field(description="Issue title")
    category: str = Field(description="Issue category (pothole, drainage, etc.)")
    severity: str = Field(description="Severity level")
    lat: float = Field(ge=-90, le=90, description="Latitude")
    lon: float = Field(ge=-180, le=180, description="Longitude")
    status: RoadIssueStatus = Field("open", description="Issue status")
    description: str | None = Field(None, description="Detailed description")
    upvotes: int = Field(0, description="Number of upvotes")
    created_at: str = Field(description="ISO 8601 creation timestamp")
    updated_at: str | None = Field(None, description="ISO 8601 last update timestamp")
    before_photo_url: str | None = Field(None, description="Before photo URL")
    after_photo_url: str | None = Field(None, description="After photo URL")


class RoadIssuesResponse(BaseModel):
    issues: list[RoadIssueItem] = Field(description="List of road issues")
    count: int = Field(description="Number of issues returned")
    page: int = Field(1, description="Current page number")
    page_size: int = Field(20, description="Items per page")
    total_pages: int = Field(1, description="Total pages available")
    total_count: int | None = Field(None, description="Total matching issues (if available)")


class RoadReportResponse(BaseModel):
    id: str = Field(description="Report identifier")
    title: str = Field(description="Report title")
    status: str = Field(description="Report status")
    submitted_at: str = Field(description="ISO 8601 submission timestamp")
    tracking_url: str = Field(description="URL to track this report")
    before_photo_url: str | None = Field(None, description="Before photo URL")
