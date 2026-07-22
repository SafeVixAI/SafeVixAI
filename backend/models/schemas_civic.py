# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Civic intelligence, ward, officer, and municipality Pydantic schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

# ── Geocoding ────────────────────────────────────────────────────────────


class GeocodeResult(BaseModel):
    lat: float = Field(description="Latitude")
    lon: float = Field(description="Longitude")
    display_name: str = Field(description="Human-readable address")
    type: str | None = Field(None, description="Location type (city, road, amenity, etc.)")


class GeocodeSearchResponse(BaseModel):
    results: list[GeocodeResult] = Field(description="Geocoding results")
    count: int = Field(description="Number of results")


# ── Complaint / Timeline ──────────────────────────────────────────────────


class ComplaintEventItem(BaseModel):
    id: str = Field(description="Event ID")
    type: str = Field(description="Event type")
    description: str = Field(description="Event description")
    timestamp: str = Field(description="ISO 8601 event timestamp")
    actor: str | None = Field(None, description="Who performed the action")


class ComplaintTimelineResponse(BaseModel):
    complaint_id: str = Field(description="Complaint ID")
    events: list[ComplaintEventItem] = Field(description="Timeline events")
    status: str = Field(description="Current status")


# ── Ward ──────────────────────────────────────────────────────────────────


class WardResponse(BaseModel):
    ward_id: str = Field(description="Ward identifier")
    name: str = Field(description="Ward name")
    municipality_id: str | None = Field(None, description="Parent municipality ID")
    lat: float | None = Field(None, description="Ward center latitude")
    lon: float | None = Field(None, description="Ward center longitude")


class WardStatsResponse(BaseModel):
    ward_id: str = Field(description="Ward identifier")
    name: str = Field(description="Ward name")
    total_issues: int = Field(0, description="Total reported issues")
    open_issues: int = Field(0, description="Open issues")
    resolved_issues: int = Field(0, description="Resolved issues")
    avg_resolution_days: float | None = Field(None, description="Average resolution time in days")
    categories: dict[str, int] = Field(default_factory=dict, description="Issues per category")


# ── Officer ────────────────────────────────────────────────────────────────


class OfficerResponse(BaseModel):
    officer_id: str = Field(description="Officer identifier")
    name: str = Field(description="Officer name")
    role: str = Field(description="Officer role")
    department: str | None = Field(None, description="Department name")
    ward: str | None = Field(None, description="Assigned ward")
    phone: str | None = Field(None, description="Contact phone")
    is_available: bool = Field(True, description="Whether officer is available")
    active_dispatches: int = Field(0, description="Active dispatch count")


class OfficerCheckinRequest(BaseModel):
    lat: float = Field(description="Check-in latitude")
    lon: float = Field(description="Check-in longitude")
    status: str | None = Field(None, description="Officer status update")


class OfficerCheckinResponse(BaseModel):
    officer_id: str = Field(description="Officer identifier")
    lat: float = Field(description="Check-in latitude")
    lon: float = Field(description="Check-in longitude")
    timestamp: str = Field(description="ISO 8601 check-in timestamp")
    status: str | None = Field(None, description="Officer status")


# ── Analytics / Heatmap ────────────────────────────────────────────────────


class HeatmapFeatureGeometry(BaseModel):
    type: str = Field("Point", description="GeoJSON geometry type")
    coordinates: list[float] = Field(description="[lon, lat] coordinates")


class HeatmapFeatureProperties(BaseModel):
    intensity: float = Field(description="Heatmap intensity 0-1")
    category: str | None = Field(None, description="Issue category")


class HeatmapFeature(BaseModel):
    type: str = Field("Feature", description="GeoJSON feature type")
    geometry: HeatmapFeatureGeometry = Field(description="Feature geometry")
    properties: HeatmapFeatureProperties = Field(description="Feature properties")


class AnalyticsHeatmapResponse(BaseModel):
    type: str = Field("FeatureCollection", description="GeoJSON type")
    features: list[HeatmapFeature] = Field(description="Heatmap features")


class WardSummaryItem(BaseModel):
    ward_id: str = Field(description="Ward identifier")
    ward_name: str = Field(description="Ward name")
    total_issues: int = Field(0, description="Total issues")
    resolved_count: int = Field(0, description="Resolved issues")
    pending_count: int = Field(0, description="Pending issues")
    avg_resolution_hours: float | None = Field(None, description="Average resolution hours")
    top_category: str | None = Field(None, description="Most common issue category")
    severity_distribution: dict[str, int] = Field(default_factory=dict, description="Severity distribution")


# ── LGD / Gov Data ─────────────────────────────────────────────────────────


class LGDEntityResponse(BaseModel):
    code: str = Field(description="LGD entity code")
    name: str = Field(description="Entity name")
    type: str = Field(description="Entity type (state, district, block, etc.)")
    parent_code: str | None = Field(None, description="Parent entity code")


class LGDHierarchyResponse(BaseModel):
    state: str | None = Field(None, description="State name")
    district: str | None = Field(None, description="District name")
    block: str | None = Field(None, description="Block name")
    panchayat: str | None = Field(None, description="Panchayat name")


# ── Civic Features ─────────────────────────────────────────────────────────


class AdminBoundaryFeature(BaseModel):
    id: int
    code: str
    name: str
    state_code: str
    area_sqkm: float | None = None
    geom_wkb: str | None = None
    geojson: dict | None = None

    @field_validator('geom_wkb', mode='before')
    @classmethod
    def validate_wkb(cls, value: str | None) -> str | None:
        if value is None:
            return None
        val_str = str(value).strip()
        if not all(c in '0123456789abcdefABCDEF' for c in val_str):
            raise ValueError("Invalid WKB: must be a valid hex string")
        return val_str

    @field_validator('geojson', mode='before')
    @classmethod
    def validate_geojson(cls, value: dict | None) -> dict | None:
        if value is None:
            return None
        if not isinstance(value, dict):
            raise ValueError("Invalid GeoJSON: must be a dictionary")
        if 'type' not in value or 'coordinates' not in value:
            raise ValueError("Invalid GeoJSON: missing 'type' or 'coordinates'")
        return value


class CivicFeatureItem(BaseModel):
    id: int
    osm_id: int
    feature_type: str
    city: str | None = None
    lat: float
    lon: float
    distance_m: float | None = None
    tags: dict | None = None


class GovDatasetRecord(BaseModel):
    id: str = Field(description="Record identifier")
    dataset_name: str = Field(description="Dataset name")
    data: dict = Field(default_factory=dict, description="Record data")
    source_url: str | None = Field(None, description="Source URL")
    ingested_at: str = Field(description="ISO 8601 ingestion timestamp")


class GrievanceItem(BaseModel):
    id: str = Field(description="Grievance identifier")
    title: str = Field(description="Grievance title")
    category: str = Field(description="Grievance category")
    status: str = Field(description="Current status")
    submitted_at: str = Field(description="ISO 8601 submission timestamp")
    description: str | None = Field(None, description="Detailed description")
    ward: str | None = Field(None, description="Assigned ward")


# ── Statistics ─────────────────────────────────────────────────────────────


class CivicStatsResponse(BaseModel):
    total_municipalities: int = Field(0, description="Total municipalities")
    total_wards: int = Field(0, description="Total wards")
    total_issues: int = Field(0, description="Total civic issues")
    resolved_issues: int = Field(0, description="Resolved issues")
    open_issues: int = Field(0, description="Open issues")
    total_officers: int = Field(0, description="Total officers")
    active_officers: int = Field(0, description="Active officers on duty")


# ── ETL ────────────────────────────────────────────────────────────────────


class ETLRunLogItem(BaseModel):
    id: str = Field(description="Run log identifier")
    pipeline: str = Field(description="Pipeline name")
    status: str = Field(description="Run status (success, failed, running)")
    started_at: str = Field(description="ISO 8601 start timestamp")
    completed_at: str | None = Field(None, description="ISO 8601 completion timestamp")
    records_processed: int = Field(0, description="Records processed")
    error_message: str | None = Field(None, description="Error message if failed")


# ── Municipality ───────────────────────────────────────────────────────────


class MunicipalityContactChannels(BaseModel):
    phone: str | None = Field(None, description="Phone number")
    email: str | None = Field(None, description="Email address")
    website: str | None = Field(None, description="Website URL")
    helpline: str | None = Field(None, description="Helpline number")


class MunicipalityLeadership(BaseModel):
    name: str = Field(description="Leader name")
    title: str = Field(description="Leadership title")


class MunicipalityLocalStats(BaseModel):
    population: int | None = Field(None, description="Population")
    area_sq_km: float | None = Field(None, description="Area in square km")
    ward_count: int = Field(0, description="Number of wards")
    literacy_rate: float | None = Field(None, description="Literacy rate percentage")


class MunicipalityListItem(BaseModel):
    id: str = Field(description="Municipality identifier")
    name: str = Field(description="Municipality name")
    state: str = Field(description="State name")
    type: str = Field(description="Municipality type (corporation, municipality, panchayat)")
    population: int | None = Field(None, description="Population")
    ward_count: int = Field(0, description="Number of wards")


class MunicipalityDetail(MunicipalityListItem):
    lat: float | None = Field(None, description="Center latitude")
    lon: float | None = Field(None, description="Center longitude")
    contact_channels: MunicipalityContactChannels | None = Field(None, description="Contact information")
    leadership: list[MunicipalityLeadership] = Field(default_factory=list, description="Leadership team")
    local_stats: MunicipalityLocalStats | None = Field(None, description="Local statistics")
