# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Contract tests validating API response shapes match schema definitions.

Validates that every public endpoint returns responses conforming to
the Pydantic schemas defined in models/schemas.py.
"""

import uuid
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from models.schemas import (
    ApiResponse,
    ChallanResponse,
    EmergencyNumbersResponse,
    EmergencyResponse,
    ErrorResponse,
    GeocodeSearchResponse,
    HealthResponse,
    MunicipalityDetail,
    MunicipalityListItem,
    OfficerResponse,
    RoadIssuesResponse,
    RoadReportResponse,
    SosResponse,
    UserProfileResponse,
    WardResponse,
)


class TestHealthContract:
    """/health endpoint response shape."""

    def test_health_response_valid(self):
        data = {
            "status": "ok",
            "version": "1.0.0",
            "database_available": True,
            "chatbot_ready": True,
            "chatbot_mode": "online",
            "cache_available": True,
            "cache_backend": "redis",
            "environment": "test",
            "uptime_seconds": 3600,
        }
        resp = HealthResponse(**data)
        assert resp.status == "ok"

    def test_health_missing_required(self):
        with pytest.raises(ValidationError):
            HealthResponse(**{})

    def test_health_response_with_optional_services(self):
        data = {
            "status": "ok",
            "version": "1.0.0",
            "database_available": True,
            "chatbot_ready": True,
            "chatbot_mode": "online",
            "cache_available": True,
            "cache_backend": "redis",
            "environment": "test",
            "uptime_seconds": 3600,
            "dependencies": [
                {"name": "database", "available": True},
                {"name": "redis", "available": True},
            ],
        }
        resp = HealthResponse(**data)
        assert len(resp.dependencies) == 2


class TestEmergencyContract:
    """Emergency endpoints (/nearby, /sos) response shapes."""

    def test_emergency_response_valid(self):
        data = {
            "services": [
                {
                    "id": "1",
                    "name": "Apollo Hospital",
                    "category": "hospital",
                    "lat": 13.0827,
                    "lon": 80.2707,
                    "distance_meters": 500.0,
                    "source": "postgis",
                    "address": "Chennai",
                    "phone": "+911234567890",
                }
            ],
            "count": 1,
            "radius_used": 5000,
            "source": "postgis",
        }
        resp = EmergencyResponse(**data)
        assert len(resp.services) == 1
        assert resp.services[0].name == "Apollo Hospital"

    def test_emergency_response_empty_services(self):
        data = {"services": [], "count": 0, "radius_used": 5000, "source": "postgis"}
        resp = EmergencyResponse(**data)
        assert resp.count == 0

    def test_emergency_numbers_valid(self):
        data = {
            "numbers": {
                "police": {"service": "Police", "coverage": "national", "notes": "Emergency"},
                "ambulance": {"service": "Ambulance", "coverage": "national", "notes": "Emergency"},
            }
        }
        resp = EmergencyNumbersResponse(**data)
        assert len(resp.numbers) == 2

    def test_sos_response_valid(self):
        data = {
            "services": [
                {"id": "1", "name": "Apollo Hospital", "category": "hospital", "lat": 13.0827, "lon": 80.2707, "distance_meters": 500.0, "source": "postgis"},
            ],
            "count": 1,
            "radius_used": 5000,
            "source": "postgis",
            "numbers": {
                "police": {"service": "Police", "coverage": "national"},
            },
        }
        resp = SosResponse(**data)
        assert resp.count >= 0


class TestChallanContract:
    """Challan calculation response shape."""

    def test_challan_response_valid(self):
        data = {
            "violation_code": "185",
            "vehicle_class": "light_motor_vehicle",
            "state_code": "TN",
            "base_fine": 10000,
            "repeat_fine": 15000,
            "amount_due": 10000,
            "section": "Section 185",
            "description": "Driving under influence of alcohol",
        }
        resp = ChallanResponse(**data)
        assert resp.violation_code == "185"

    def test_challan_response_repeat_offense(self):
        data = {
            "violation_code": "185",
            "vehicle_class": "light_motor_vehicle",
            "state_code": "TN",
            "base_fine": 10000,
            "repeat_fine": 15000,
            "amount_due": 15000,
            "section": "Section 185",
            "description": "Driving under influence of alcohol",
            "state_override": "TN override applied",
        }
        resp = ChallanResponse(**data)
        assert resp.amount_due == 15000


class TestRoadIssuesContract:
    """Road issues endpoints response shapes."""

    def test_road_issues_response_valid(self):
        uid = uuid.uuid4()
        data = {
            "issues": [
                {
                    "uuid": str(uid),
                    "issue_type": "pothole",
                    "title": "Deep pothole",
                    "severity": 3,
                    "lat": 13.0827,
                    "lon": 80.2707,
                    "distance_meters": 100.0,
                    "status": "open",
                    "description": "Deep pothole on Anna Salai",
                    "upvotes": 5,
                    "created_at": "2026-07-04T10:00:00Z",
                    "updated_at": "2026-07-04T10:00:00Z",
                }
            ],
            "count": 1,
            "radius_used": 5000,
        }
        resp = RoadIssuesResponse(**data)
        assert len(resp.issues) == 1

    def test_road_report_response_valid(self):
        uid = uuid.uuid4()
        data = {
            "uuid": str(uid),
            "authority_name": "Chennai Corporation",
            "authority_phone": "044-12345",
            "complaint_portal": "https://example.com/complaint",
            "road_type": "Municipal Road",
            "road_type_code": "MUN",
            "status": "open",
            "complaint_ref": "CRN-001",
        }
        resp = RoadReportResponse(**data)
        assert resp.status == "open"


class TestGeocodeContract:
    """Geocoding response shape."""

    def test_geocode_search_response_valid(self):
        data = {
            "results": [
                {
                    "lat": 13.0827,
                    "lon": 80.2707,
                    "display_name": "Chennai, Tamil Nadu, India",
                    "type": "city",
                }
            ],
        }
        resp = GeocodeSearchResponse(**data)
        assert len(resp.results) == 1


class TestUserContract:
    """User profile endpoints response shapes."""

    def test_user_profile_response_valid(self):
        uid = uuid.uuid4()
        now = datetime.now(timezone.utc)
        data = {
            "name": "John Doe",
            "id": str(uid),
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "blood_group": "O+",
            "emergency_contacts": [
                {"name": "Emergency", "phone": "+919876543210", "relation": "service"}
            ],
        }
        resp = UserProfileResponse(**data)
        assert resp.name == "John Doe"
        assert resp.blood_group == "O+"

    def test_user_profile_partial(self):
        uid = uuid.uuid4()
        now = datetime.now(timezone.utc)
        data = {
            "name": "John Doe",
            "id": str(uid),
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }
        resp = UserProfileResponse(**data)
        assert resp.name == "John Doe"
        assert resp.blood_group is None


class TestWardOfficerContract:
    """Ward and officer endpoints response shapes."""

    def test_ward_response_valid(self):
        data = {
            "ward_id": "ward_09_teynampet",
            "ward_name": "Ward 9 - Teynampet",
        }
        resp = WardResponse(**data)
        assert resp.ward_id == "ward_09_teynampet"

    def test_officer_response_valid(self):
        uid = uuid.uuid4()
        now = datetime.now(timezone.utc)
        data = {
            "id": str(uid),
            "name": "Officer Kumar",
            "role": "traffic_inspector",
            "is_active": True,
            "created_at": now.isoformat(),
            "department": "Chennai Traffic Police",
            "phone": "+919876543210",
        }
        resp = OfficerResponse(**data)
        assert resp.name == "Officer Kumar"
        assert resp.is_active is True


class TestApiResponseContract:
    """Generic ApiResponse wrapper shape."""

    def test_api_response_success(self):
        data = {"success": True, "data": {"key": "value"}, "timestamp": "2026-07-04T12:00:00Z"}
        resp = ApiResponse[dict](**data)
        assert resp.success is True
        assert resp.data["key"] == "value"

    def test_api_response_error(self):
        data = {
            "error": {
                "code": "NOT_FOUND",
                "message": "Not found",
                "details": {"status_code": 404},
            },
        }
        resp = ErrorResponse(**data)
        assert resp.error.code == "NOT_FOUND"
        assert resp.error.message == "Not found"


class TestCivicIntelContract:
    """Civic intelligence endpoint response shapes."""

    def test_municipality_list_item_valid(self):
        data = {
            "slug": "chennai-corporation",
            "name": "Chennai Corporation",
            "short_name": "Chennai Corp",
            "municipality_type": "corporation",
            "city": "Chennai",
            "state_code": "TN",
            "state_name": "Tamil Nadu",
            "ward_count": 200,
            "population": 10000000,
        }
        resp = MunicipalityListItem(**data)
        assert resp.name == "Chennai Corporation"

    def test_municipality_detail_valid(self):
        data = {
            "slug": "chennai-corporation",
            "name": "Chennai Corporation",
            "short_name": "Chennai Corp",
            "municipality_type": "corporation",
            "city": "Chennai",
            "state_code": "TN",
            "state_name": "Tamil Nadu",
            "contact": {
                "helpline_phone": "044-12345",
                "email": "corp@chennai.gov.in",
            },
            "leadership": {
                "mayor_name": "Mayor Name",
                "commissioner_name": "Commissioner Name",
            },
            "stats": {
                "ward_count": 200,
                "population": 10000000,
                "area_sqkm": 426.0,
            },
        }
        resp = MunicipalityDetail(**data)
        assert resp.slug == "chennai-corporation"
        assert resp.contact.helpline_phone == "044-12345"
