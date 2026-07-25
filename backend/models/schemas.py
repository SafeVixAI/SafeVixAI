# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

from datetime import date, datetime
from typing import Generic, Literal, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

EmergencyCategory = Literal['hospital', 'police', 'ambulance', 'fire', 'towing', 'pharmacy', 'puncture', 'showroom']
RoadIssueStatus = Literal['open', 'acknowledged', 'in_progress', 'resolved', 'rejected', 'pending_processing', 'verified']
RouteProfile = Literal['driving-car', 'cycling-regular', 'foot-walking']
BloodGroup = Literal['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']


class DependencyHealth(BaseModel):
    name: str
    available: bool
    latency_ms: float | None = None
    error: str | None = None


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict | None = None


class ErrorResponse(BaseModel):
    error: ErrorDetail


class HealthResponse(BaseModel):
    status: str
    database_available: bool
    chatbot_ready: bool
    chatbot_mode: str
    cache_available: bool
    cache_backend: str
    environment: str
    version: str
    dependencies: list[DependencyHealth] | None = None
    circuit_breakers: dict[str, str] | None = None
    pool_stats: dict[str, int] | None = None
    uptime_seconds: float | None = None


class EmergencyNumber(BaseModel):
    service: str
    coverage: str
    notes: str | None = None


class EmergencyNumbersResponse(BaseModel):
    numbers: dict[str, EmergencyNumber]


class EmergencyServiceItem(BaseModel):
    id: str
    name: str
    category: str
    sub_category: str | None = None
    phone: str | None = None
    phone_emergency: str | None = None
    lat: float
    lon: float
    distance_meters: float
    has_trauma: bool = False
    has_icu: bool = False
    is_24hr: bool = True
    address: str | None = None
    source: str = 'database'


class EmergencyResponse(BaseModel):
    services: list[EmergencyServiceItem]
    count: int
    radius_used: int
    source: str
    next_offset: int | None = None
    total_count: int | None = None


class SosResponse(BaseModel):
    services: list[EmergencyServiceItem]
    count: int
    radius_used: int
    source: str
    numbers: dict[str, EmergencyNumber]


class GeocodeResult(BaseModel):
    display_name: str
    city: str | None = None
    state: str | None = None
    state_code: str | None = None
    country_code: str | None = None
    postcode: str | None = None
    lat: float | None = None
    lon: float | None = None


class GeocodeSearchResponse(BaseModel):
    results: list[GeocodeResult]


class AuthorityPreviewResponse(BaseModel):
    road_type: str
    road_type_code: str
    road_name: str | None = None
    road_number: str | None = None
    authority_name: str
    helpline: str
    complaint_portal: str
    escalation_path: str
    exec_engineer: str | None = None
    exec_engineer_phone: str | None = None
    contractor_name: str | None = None
    budget_sanctioned: int | None = None
    budget_spent: int | None = None
    last_relayed_date: date | None = None
    next_maintenance: date | None = None
    data_source_url: str | None = None
    source: str = 'authority_matrix'


class RoadInfrastructureResponse(BaseModel):
    road_type: str
    road_type_code: str
    road_name: str | None = None
    road_number: str | None = None
    contractor_name: str | None = None
    exec_engineer: str | None = None
    exec_engineer_phone: str | None = None
    budget_sanctioned: int | None = None
    budget_spent: int | None = None
    last_relayed_date: date | None = None
    next_maintenance: date | None = None
    data_source_url: str | None = None
    source: str


class RoadIssueItem(BaseModel):
    uuid: UUID
    complaint_ref: str | None = None
    issue_type: str
    severity: int
    description: str | None = None
    lat: float
    lon: float
    location_address: str | None = None
    road_name: str | None = None
    road_type: str | None = None
    road_number: str | None = None
    authority_name: str | None = None
    status: RoadIssueStatus
    created_at: datetime
    distance_meters: float

    # Enterprise fields
    category: str | None = None
    sub_category: str | None = None
    ward_id: str | None = None
    ward_name: str | None = None
    assigned_officer_id: UUID | None = None
    sla_deadline: datetime | None = None
    resolved_at: datetime | None = None
    duplicate_of_uuid: UUID | None = None
    confirmation_count: int = 0
    before_photo_url: str | None = None
    after_photo_url: str | None = None


class RoadIssuesResponse(BaseModel):
    issues: list[RoadIssueItem]
    count: int
    radius_used: int
    next_offset: int | None = None
    total_count: int | None = None


class RoadReportResponse(BaseModel):
    uuid: UUID
    complaint_ref: str | None = None
    authority_name: str
    authority_phone: str
    complaint_portal: str
    road_type: str
    road_type_code: str
    road_number: str | None = None
    road_name: str | None = None
    exec_engineer: str | None = None
    exec_engineer_phone: str | None = None
    contractor_name: str | None = None
    last_relayed_date: date | None = None
    next_maintenance: date | None = None
    budget_sanctioned: int | None = None
    budget_spent: int | None = None
    photo_url: str | None = None
    status: RoadIssueStatus
    ai_detection: dict | None = None

    # Enterprise fields
    category: str | None = None
    sub_category: str | None = None
    ward_id: str | None = None
    ward_name: str | None = None
    sla_deadline: datetime | None = None
    duplicate_of_uuid: UUID | None = None


class RoutePoint(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    label: str | None = Field(default=None, max_length=120)


class RouteBounds(BaseModel):
    south: float
    west: float
    north: float
    east: float


class RouteInstruction(BaseModel):
    index: int
    instruction: str
    distance_meters: float
    duration_seconds: float
    street_name: str | None = None
    instruction_type: int | None = None
    exit_number: int | None = None


class RouteOption(BaseModel):
    route_id: str
    label: str
    distance_meters: float
    duration_seconds: float
    path: list[RoutePoint]
    bounds: RouteBounds
    steps: list[RouteInstruction] = Field(default_factory=list)


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


class ServiceCandidate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    category: str
    lat: float
    lon: float
    distance_meters: float
    address: str | None = None
    phone: str | None = None
    source: str


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    session_id: str | None = Field(default=None, min_length=1, max_length=128)
    lat: float | None = Field(default=None, ge=-90, le=90)
    lon: float | None = Field(default=None, ge=-180, le=180)
    client_ip: str | None = Field(default=None)
    provider_hint: str | None = Field(default=None, max_length=64)
    provider_model: str | None = Field(default=None, max_length=128)
    user_id: str | None = Field(default=None, max_length=128)


class ChatResponse(BaseModel):
    response: str
    intent: str | None = None
    sources: list[str] = Field(default_factory=list)
    session_id: str


class ChallanQuery(BaseModel):
    violation_code: str = Field(min_length=1, max_length=32)
    vehicle_class: str = Field(min_length=1, max_length=32)
    state_code: str = Field(min_length=1, max_length=64)
    is_repeat: bool = False


class ChallanResponse(BaseModel):
    violation_code: str
    vehicle_class: str
    state_code: str
    base_fine: int
    repeat_fine: int | None = None
    amount_due: int
    section: str
    description: str
    state_override: str | None = None


class EmergencyContact(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    phone: str = Field(min_length=7, max_length=20, pattern=r'^\+?[0-9][0-9\s-]{5,18}[0-9]$')
    relation: str | None = Field(default=None, max_length=40)


class UserProfileCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    blood_group: BloodGroup | None = None
    emergency_contacts: list[EmergencyContact] = Field(default_factory=list, max_length=5)
    allergies: str | None = Field(default=None, max_length=500)
    vehicle_details: str | None = Field(default=None, max_length=120)
    medical_notes: str | None = Field(default=None, max_length=1000)

    @field_validator('blood_group', mode='before')
    @classmethod
    def normalize_blood_group(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().upper().replace(' POSITIVE', '+').replace(' NEGATIVE', '-')
        normalized = normalized.replace('POSITIVE', '+').replace('NEGATIVE', '-').replace(' ', '')
        return normalized


class UserProfileUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=80)
    blood_group: BloodGroup | None = None
    emergency_contacts: list[EmergencyContact] | None = Field(default=None, max_length=5)
    allergies: str | None = Field(default=None, max_length=500)
    vehicle_details: str | None = Field(default=None, max_length=120)
    medical_notes: str | None = Field(default=None, max_length=1000)

    @field_validator('blood_group', mode='before')
    @classmethod
    def normalize_blood_group(cls, value: str | None) -> str | None:
        return UserProfileCreate.normalize_blood_group(value)


class UserProfileResponse(UserProfileCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    created_at: datetime
    updated_at: datetime


class UserDataExport(BaseModel):
    profile: UserProfileResponse
    sos_incidents: list[dict] = []
    road_reports: list[dict] = []
    total_exported_at: datetime = Field(default_factory=lambda: datetime.now())


class UserDeleteResponse(BaseModel):
    status: str
    message: str
    deleted_profile: bool
    deleted_sos_incidents: int
    deleted_road_reports: int


# Enterprise Schemas
ComplaintCategory = Literal['roads', 'traffic', 'streetlight']


class ComplaintEventItem(BaseModel):
    id: int
    complaint_uuid: UUID
    event_type: str
    actor_id: UUID | None = None
    actor_role: str | None = None
    notes: str | None = None
    metadata: dict | None = None
    created_at: datetime


class ComplaintTimelineResponse(BaseModel):
    timeline: list[ComplaintEventItem]
    count: int


class WardResponse(BaseModel):
    ward_id: str
    ward_name: str
    zone_name: str | None = None
    city: str | None = None
    state_code: str | None = None
    population: int | None = None
    area_sqkm: float | None = None


class WardStatsResponse(BaseModel):
    ward_id: str
    open_issues: int
    resolved_issues: int
    rejected_issues: int
    total_issues: int
    resolution_rate: float


class OfficerResponse(BaseModel):
    id: UUID
    name: str
    phone: str | None = None
    email: str | None = None
    role: str
    ward_id: str | None = None
    department: str | None = None
    is_active: bool
    last_checkin: datetime | None = None
    created_at: datetime


class OfficerCheckinRequest(BaseModel):
    lat: float
    lon: float


class OfficerCheckinResponse(BaseModel):
    status: str
    last_checkin: datetime


class HeatmapFeatureGeometry(BaseModel):
    type: Literal['Point'] = 'Point'
    coordinates: list[float]  # [lon, lat]


class HeatmapFeatureProperties(BaseModel):
    uuid: UUID
    category: str
    severity: int
    status: str


class HeatmapFeature(BaseModel):
    type: Literal['Feature'] = 'Feature'
    geometry: HeatmapFeatureGeometry
    properties: HeatmapFeatureProperties


class AnalyticsHeatmapResponse(BaseModel):
    type: Literal['FeatureCollection'] = 'FeatureCollection'
    features: list[HeatmapFeature]


class WardSummaryItem(BaseModel):
    ward_id: str
    ward_name: str
    zone_name: str | None = None
    open_issues: int
    resolved_issues: int
    resolution_rate: float
    sla_breach_count: int


# ════════════════════════════════════════════════════════════
# CIVIC INTELLIGENCE SCHEMAS
# ════════════════════════════════════════════════════════════

CivicEntityType = Literal[
    'state', 'district', 'subdistrict', 'block', 'ulb', 'gp', 'village',
]
BoundaryLevel = Literal['state', 'district', 'subdistrict', 'ward']
CivicFeatureType = Literal[
    'streetlight', 'traffic_signal', 'bus_stop', 'speed_bump',
    'cctv', 'zebra_crossing', 'toll_booth',
]
MunicipalityType = Literal[
    'municipal_corporation', 'municipality', 'town_panchayat', 'cantonment_board',
]


class LGDEntityResponse(BaseModel):
    lgd_code: int
    entity_type: CivicEntityType
    name_en: str
    name_local: str | None = None
    state_code: str
    parent_lgd_code: int | None = None
    census_code_2011: str | None = None
    population_census_2011: int | None = None


class LGDHierarchyResponse(BaseModel):
    state_code: str
    hierarchy: dict[str, list[dict]]


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
            msg = "Invalid WKB: must be a valid hex string"
            raise ValueError(msg)
        return val_str

    @field_validator('geojson', mode='before')
    @classmethod
    def validate_geojson(cls, value: dict | None) -> dict | None:
        if value is None:
            return None
        if not isinstance(value, dict):
            msg = "Invalid GeoJSON: must be a dictionary"
            raise ValueError(msg)
        if 'type' not in value or 'coordinates' not in value:
            msg = "Invalid GeoJSON: missing 'type' or 'coordinates'"
            raise ValueError(msg)
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
    id: int
    dataset_slug: str
    year: int | None = None
    state_code: str | None = None
    district_name: str | None = None
    metric_name: str | None = None
    metric_value: float | None = None
    unit: str | None = None
    data: dict | None = None


class GrievanceItem(BaseModel):
    id: int
    source: str
    grievance_ref: str
    category: str
    subcategory: str | None = None
    description: str
    state_code: str | None = None
    district: str | None = None
    status: str
    filed_at: datetime | None = None
    resolved_at: datetime | None = None


class CivicStatsResponse(BaseModel):
    state_code: str | None = None
    lgd_entities: int = 0
    admin_boundaries: int = 0
    osm_features: dict[str, int] = {}
    grievances: dict[str, int] = {}
    municipalities: int = 0


class ETLRunLogItem(BaseModel):
    id: int
    pipeline: str
    started_at: datetime
    finished_at: datetime | None = None
    status: str
    records_fetched: int = 0
    records_inserted: int = 0
    records_updated: int = 0
    records_skipped: int = 0
    error: str | None = None


class MunicipalityContactChannels(BaseModel):
    headquarters_address: str | None = None
    helpline_phone: str | None = None
    whatsapp_number: str | None = None
    email: str | None = None
    website_url: str | None = None
    app_name: str | None = None
    app_url: str | None = None
    grievance_portal_url: str | None = None


class MunicipalityLeadership(BaseModel):
    mayor_name: str | None = None
    mayor_photo_url: str | None = None
    commissioner_name: str | None = None
    commissioner_phone: str | None = None


class MunicipalityLocalStats(BaseModel):
    ward_count: int | None = None
    population: int | None = None
    area_sqkm: float | None = None


class MunicipalityListItem(BaseModel):
    slug: str
    name: str
    short_name: str
    municipality_type: str
    city: str
    state_code: str
    state_name: str
    ward_count: int | None = None
    population: int | None = None
    helpline_phone: str | None = None


class MunicipalityDetail(BaseModel):
    slug: str
    name: str
    short_name: str
    municipality_type: str
    city: str
    state_code: str
    state_name: str
    lgd_code: int | None = None
    district_name: str | None = None
    contact: MunicipalityContactChannels
    leadership: MunicipalityLeadership
    stats: MunicipalityLocalStats
    geo: dict[str, float | None] = {}
    description: str | None = None
    services_offered: dict | None = None
    last_verified: str | None = None


T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    success: bool = True
    data: T | None = None
    error: dict | None = None
    timestamp: str = ""

    model_config = {"arbitrary_types_allowed": True}


class ApiErrorResponse(BaseModel):
    success: bool = False
    data: None = None
    error: dict
    timestamp: str = ""


# ════════════════════════════════════════════════════════════
# ENTERPRISE EXTENSION SCHEMAS: GARAGE, DISPUTE, PREDICTION
# ════════════════════════════════════════════════════════════

class VehicleGarageItem(BaseModel):
    id: UUID
    vehicle_number: str
    owner_name: str
    vehicle_make: str
    vehicle_model: str
    rc_status: str
    insurance_expiry: datetime | None = None
    puc_expiry: datetime | None = None
    created_at: datetime


class GarageSyncResponse(BaseModel):
    vehicles: list[VehicleGarageItem]
    sync_status: str
    last_synced_at: datetime


class TelemetryDataPoint(BaseModel):
    speeding_events: int = 0
    harsh_braking_events: int = 0
    night_driving_minutes: int = 0
    total_km_driven: float = 0.0


class FinePredictionRequest(BaseModel):
    vehicle_number: str
    state_code: str
    telemetry: TelemetryDataPoint


class FinePredictionResponse(BaseModel):
    predicted_violations_count: int
    estimated_annual_liability: int
    risk_score: float
    risk_level: Literal['low', 'medium', 'high']
    recommendations: list[str]


class DisputeDraftRequest(BaseModel):
    challan_ref: str
    violation_code: str
    fine_amount: int
    mitigating_factors: str


class DisputeDraftResponse(BaseModel):
    dispute_ref: str
    appeal_letter: str
    cited_mva_sections: list[str]
    confidence_score: float
    instructions: list[str]
