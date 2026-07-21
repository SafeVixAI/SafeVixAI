# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone, timedelta

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import select

from core.database import get_db as core_get_db
from core.limiter import limiter
from models.road_issue import RoadIssue
from services.complaint_state_machine import InvalidTransitionError


@pytest.fixture(autouse=True)
def disable_limiter():
    limiter.enabled = False
    yield


# ── Helpers ─────────────────────────────────────────────────────────────────

def _mock_execute_result(scalar_one_or_none_value=None, scalars_all_value=None):
    """Create a mock execute result with scalars and scalar_one_or_none."""
    result = MagicMock()
    result.scalar_one_or_none.return_value = scalar_one_or_none_value
    if scalars_all_value is not None:
        result.scalars.return_value.all.return_value = scalars_all_value
    return result


def _mock_db_session(execute_result=None, side_effect=None):
    """Create a mock DB session."""
    session = AsyncMock()
    if side_effect:
        session.execute = AsyncMock(side_effect=side_effect)
    else:
        session.execute = AsyncMock(return_value=execute_result)
    session.commit = AsyncMock()
    session.add = MagicMock()
    return session


# ── Officers API tests ──────────────────────────────────────────────────────

_OFFICER_USER_ID = "00000000-0000-0000-0000-000000000001"

@pytest.fixture
def officers_app():
    app = FastAPI()
    from api.v1.officers import router, get_current_user
    app.include_router(router)
    app.dependency_overrides[get_current_user] = lambda: {"sub": _OFFICER_USER_ID, "email": "officer@test.com", "name": "John"}
    return app


class TestOfficersAPI:
    def test_get_me_auto_provisions(self, officers_app):
        client = TestClient(officers_app)
        exec_result = _mock_execute_result(scalar_one_or_none_value=None)
        db = _mock_db_session(exec_result)

        created_instances = []
        def add_side_effect(inst):
            created_instances.append(inst)
            now = datetime.utcnow()
            if getattr(inst, 'created_at', None) is None:
                inst.created_at = now
            if getattr(inst, 'last_checkin', None) is None:
                inst.last_checkin = now
        db.add.side_effect = add_side_effect

        async def get_db_override():
            yield db

        officers_app.dependency_overrides[core_get_db] = get_db_override
        with patch("api.v1.officers.get_settings") as s:
            s.return_value.default_officer_ward = "1"
            response = client.get("/api/v1/officers/me")

        assert response.status_code not in (500,)
        db.commit.assert_called()

    def test_get_me_returns_existing(self, officers_app):
        client = TestClient(officers_app)
        mock_officer = MagicMock()
        mock_officer.id = uuid.UUID("00000000-0000-0000-0000-000000000001")
        mock_officer.name = "John"
        mock_officer.phone = "1234567890"
        mock_officer.email = "john@test.com"
        mock_officer.role = "field_officer"
        mock_officer.ward_id = "1"
        mock_officer.department = "PWD"
        mock_officer.is_active = True
        mock_officer.last_checkin = None
        mock_officer.created_at = datetime(2026, 1, 1)

        exec_result = _mock_execute_result(scalar_one_or_none_value=mock_officer)
        db = _mock_db_session(exec_result)

        async def get_db_override():
            yield db

        officers_app.dependency_overrides[core_get_db] = get_db_override
        response = client.get("/api/v1/officers/me")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "John"
        assert data["email"] == "john@test.com"

    def test_checkin_success(self, officers_app):
        client = TestClient(officers_app)
        mock_officer = MagicMock()
        mock_officer.id = "uid"
        mock_officer.name = "John"
        mock_officer.lat = None
        mock_officer.lon = None

        exec_result = _mock_execute_result(scalar_one_or_none_value=mock_officer)
        db = _mock_db_session(exec_result)

        async def get_db_override():
            yield db

        officers_app.dependency_overrides[core_get_db] = get_db_override
        response = client.post(
            "/api/v1/officers/checkin",
            json={"lat": 13.0, "lon": 80.0},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

    def test_workload(self, officers_app):
        client = TestClient(officers_app)
        mock_officer = MagicMock()
        mock_officer.id = "uid"
        mock_officer.ward_id = 1

        exec_result = _mock_execute_result(scalar_one_or_none_value=mock_officer)
        db = _mock_db_session(exec_result)

        async def get_db_override():
            yield db

        officers_app.dependency_overrides[core_get_db] = get_db_override
        response = client.get("/api/v1/officers/me/workload")
        assert response.status_code == 200


# ── Citizen API tests ───────────────────────────────────────────────────────

@pytest.fixture
def citizen_app():
    app = FastAPI()
    from api.v1.citizen import router, get_db
    app.include_router(router)
    return app


class TestCitizenAPI:
    def test_track_complaint_found(self, citizen_app):
        client = TestClient(citizen_app)
        mock_issue = MagicMock(spec=RoadIssue)
        mock_issue.complaint_ref = "CMP-001"
        mock_issue.status = "open"
        mock_issue.sla_deadline = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=2)
        mock_issue.created_at = datetime(2026, 1, 1)
        mock_issue.resolved_at = None
        mock_issue.confirmation_count = 0
        mock_issue.uuid = "uuid-1"
        mock_issue.location = None
        mock_issue.category = mock_issue.issue_type = mock_issue.description = mock_issue.location_address = ""
        mock_issue.ward_name = mock_issue.road_name = mock_issue.authority_name = ""
        mock_issue.before_photo_url = mock_issue.after_photo_url = None
        mock_issue.severity = 3

        exec_result = _mock_execute_result(scalar_one_or_none_value=mock_issue)
        db = _mock_db_session(exec_result)

        from api.v1.citizen import get_db as citizen_get_db
        async def get_db_override():
            yield db
        citizen_app.dependency_overrides[citizen_get_db] = get_db_override

        response = client.get("/api/v1/citizen/complaints/CMP-001")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "open"

    def test_track_complaint_sla_breached(self, citizen_app):
        client = TestClient(citizen_app)
        mock_issue = MagicMock(spec=RoadIssue)
        mock_issue.complaint_ref = "CMP-002"
        mock_issue.status = "open"
        mock_issue.sla_deadline = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=2)
        mock_issue.created_at = datetime(2026, 1, 1)
        mock_issue.resolved_at = None
        mock_issue.confirmation_count = 0
        mock_issue.uuid = "uuid-2"
        mock_issue.location = None
        mock_issue.category = mock_issue.issue_type = mock_issue.description = mock_issue.location_address = ""
        mock_issue.ward_name = mock_issue.road_name = mock_issue.authority_name = ""
        mock_issue.before_photo_url = mock_issue.after_photo_url = None

        exec_result = _mock_execute_result(scalar_one_or_none_value=mock_issue)
        db = _mock_db_session(exec_result)

        from api.v1.citizen import get_db as citizen_get_db
        async def get_db_override():
            yield db
        citizen_app.dependency_overrides[citizen_get_db] = get_db_override

        response = client.get("/api/v1/citizen/complaints/CMP-002")
        assert response.status_code == 200
        assert response.json()["sla_status"] == "breached"

    def test_track_complaint_not_found(self, citizen_app):
        client = TestClient(citizen_app)
        exec_result = _mock_execute_result(scalar_one_or_none_value=None)
        db = _mock_db_session(exec_result)

        from api.v1.citizen import get_db as citizen_get_db
        async def get_db_override():
            yield db
        citizen_app.dependency_overrides[citizen_get_db] = get_db_override

        response = client.get("/api/v1/citizen/complaints/NONEXISTENT")
        assert response.status_code == 404

    def test_confirm_resolution_success(self, citizen_app):
        client = TestClient(citizen_app)
        mock_issue = MagicMock(spec=RoadIssue)
        mock_issue.uuid = "uuid-1"
        mock_issue.status = "resolved"
        mock_issue.complaint_ref = "CMP-001"

        exec_result = _mock_execute_result(scalar_one_or_none_value=mock_issue)
        db = _mock_db_session(exec_result)

        from api.v1.citizen import get_db as citizen_get_db
        async def get_db_override():
            yield db
        citizen_app.dependency_overrides[citizen_get_db] = get_db_override

        with patch("api.v1.citizen.ComplaintStateMachine.transition", AsyncMock()):
            response = client.post(
                "/api/v1/citizen/complaints/CMP-001/confirm",
                json={"citizen_phone": "+911234567890"},
            )
        assert response.status_code == 200

    def test_confirm_resolution_wrong_status(self, citizen_app):
        client = TestClient(citizen_app)
        mock_issue = MagicMock(spec=RoadIssue)
        mock_issue.uuid = "uuid-1"
        mock_issue.status = "open"
        mock_issue.complaint_ref = "CMP-001"

        exec_result = _mock_execute_result(scalar_one_or_none_value=mock_issue)
        db = _mock_db_session(exec_result)

        from api.v1.citizen import get_db as citizen_get_db
        async def get_db_override():
            yield db
        citizen_app.dependency_overrides[citizen_get_db] = get_db_override

        response = client.post(
            "/api/v1/citizen/complaints/CMP-001/confirm",
            json={},
        )
        assert response.status_code == 409

    def test_reject_resolution_success(self, citizen_app):
        client = TestClient(citizen_app)
        mock_issue = MagicMock(spec=RoadIssue)
        mock_issue.uuid = "uuid-1"
        mock_issue.status = "resolved"
        mock_issue.complaint_ref = "CMP-001"
        mock_issue.severity = 3

        exec_result = _mock_execute_result(scalar_one_or_none_value=mock_issue)
        db = _mock_db_session(exec_result)

        from api.v1.citizen import get_db as citizen_get_db
        async def get_db_override():
            yield db
        citizen_app.dependency_overrides[citizen_get_db] = get_db_override

        with patch("api.v1.citizen.ComplaintStateMachine.transition", AsyncMock()):
            response = client.post(
                "/api/v1/citizen/complaints/CMP-001/reject",
                json={"reason": "The pothole is still there and very dangerous"},
            )
        assert response.status_code == 200
        assert response.json()["status"] == "reopened"

    def test_reject_resolution_wrong_status(self, citizen_app):
        client = TestClient(citizen_app)
        mock_issue = MagicMock()
        mock_issue.uuid = "uuid-1"
        mock_issue.status = "open"
        mock_issue.complaint_ref = "CMP-001"

        exec_result = _mock_execute_result(scalar_one_or_none_value=mock_issue)
        db = _mock_db_session(exec_result)

        from api.v1.citizen import get_db as citizen_get_db
        async def get_db_override():
            yield db
        citizen_app.dependency_overrides[citizen_get_db] = get_db_override

        response = client.post(
            "/api/v1/citizen/complaints/CMP-001/reject",
            json={"reason": "Not satisfied with the resolution quality"},
        )
        assert response.status_code == 409

    def test_rate_resolution(self, citizen_app):
        client = TestClient(citizen_app)
        mock_issue = MagicMock(spec=RoadIssue)
        mock_issue.uuid = "uuid-1"
        mock_issue.status = "closed"
        mock_issue.complaint_ref = "CMP-001"
        mock_issue.citizen_rating = None

        exec_result = _mock_execute_result(scalar_one_or_none_value=mock_issue)
        db = _mock_db_session(exec_result)

        from api.v1.citizen import get_db as citizen_get_db
        async def get_db_override():
            yield db
        citizen_app.dependency_overrides[citizen_get_db] = get_db_override

        response = client.post(
            "/api/v1/citizen/complaints/CMP-001/rate",
            json={"rating": 4, "feedback": "Good work"},
        )
        assert response.status_code == 200
        assert response.json()["rating"] == 4

    def test_rate_wrong_status(self, citizen_app):
        client = TestClient(citizen_app)
        mock_issue = MagicMock()
        mock_issue.uuid = "uuid-1"
        mock_issue.status = "open"
        mock_issue.complaint_ref = "CMP-001"

        exec_result = _mock_execute_result(scalar_one_or_none_value=mock_issue)
        db = _mock_db_session(exec_result)

        from api.v1.citizen import get_db as citizen_get_db
        async def get_db_override():
            yield db
        citizen_app.dependency_overrides[citizen_get_db] = get_db_override

        response = client.post(
            "/api/v1/citizen/complaints/CMP-001/rate",
            json={"rating": 3},
        )
        assert response.status_code == 409

    def test_timeline(self, citizen_app):
        client = TestClient(citizen_app)
        mock_issue = MagicMock()
        mock_issue.uuid = "uuid-1"
        mock_issue.status = "resolved"
        mock_issue.complaint_ref = "CMP-001"

        mock_event = MagicMock()
        mock_event.event_type = "status_change"
        mock_event.actor_role = "officer"
        mock_event.notes = "Assigned to John"
        mock_event.created_at = datetime(2026, 1, 1)

        exec_issue = _mock_execute_result(scalar_one_or_none_value=mock_issue)
        exec_events = _mock_execute_result(scalars_all_value=[mock_event])

        call_count = [0]

        def side_effect(*a, **kw):
            call_count[0] += 1
            if call_count[0] == 1:
                return exec_issue
            return exec_events

        db = _mock_db_session(side_effect=side_effect)

        from api.v1.citizen import get_db as citizen_get_db
        async def get_db_override():
            yield db
        citizen_app.dependency_overrides[citizen_get_db] = get_db_override

        response = client.get("/api/v1/citizen/complaints/CMP-001/timeline")
        assert response.status_code == 200
        data = response.json()
        assert "timeline" in data
        assert data["current_status"] == "resolved"

    def test_confirm_transition_error(self, citizen_app):
        client = TestClient(citizen_app)
        mock_issue = MagicMock()
        mock_issue.uuid = "uuid-1"
        mock_issue.status = "resolved"
        mock_issue.complaint_ref = "CMP-001"

        exec_result = _mock_execute_result(scalar_one_or_none_value=mock_issue)
        db = _mock_db_session(exec_result)

        from api.v1.citizen import get_db as citizen_get_db
        async def get_db_override():
            yield db
        citizen_app.dependency_overrides[citizen_get_db] = get_db_override

        with patch("api.v1.citizen.ComplaintStateMachine.transition",
                   AsyncMock(side_effect=InvalidTransitionError("open", "resolved", "CMP-001"))):
            response = client.post(
                "/api/v1/citizen/complaints/CMP-001/confirm",
                json={},
            )
        assert response.status_code == 409


# ── Offline API tests ───────────────────────────────────────────────────────

@pytest.fixture
def offline_app():
    app = FastAPI()
    from api.v1.offline import router
    app.include_router(router)
    app.state.emergency_service = MagicMock()
    app.state.emergency_service.build_city_bundle = AsyncMock(return_value={"city": "chennai", "hospitals": []})
    return app


class TestOfflineAPI:
    def test_bundle_success(self, offline_app):
        client = TestClient(offline_app)
        response = client.get("/api/v1/offline/bundle/chennai")
        assert response.status_code == 200
        assert response.json()["city"] == "chennai"

    def test_bundle_not_found(self, offline_app):
        client = TestClient(offline_app)
        from services.exceptions import ServiceValidationError
        offline_app.state.emergency_service.build_city_bundle = AsyncMock(
            side_effect=ServiceValidationError("City not found")
        )
        response = client.get("/api/v1/offline/bundle/unknown")
        assert response.status_code == 404
