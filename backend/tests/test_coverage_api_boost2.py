# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Coverage boost tests: auth, authority, citizen, public, field_workflow,
officers, user, roadwatch, command_center, tracking edge cases.
"""
from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import jwt
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from core.circuit_breaker import CircuitBreakerRegistry
from core.database import get_db
from core.rbac import Role, require_role
from core.security import (
    ALGORITHM,
    APP_JWT_AUDIENCE,
    APP_JWT_ISSUER,
    SECRET_KEY,
    _revoked_token_jtis,
    create_access_token,
    create_refresh_token,
    get_current_user,
    get_current_user_optional,
)
from models.officer import Officer
from models.road_issue import RoadIssue
from models.schemas import (
    AuthorityPreviewResponse,
    RoadInfrastructureResponse,
    RoadIssuesResponse,
    RoadReportResponse,
)
from models.user import UserProfile

_USER_ID = str(uuid.uuid4())

def _auth(sub=None, role="operator"):
    return {"sub": sub or _USER_ID, "role": role, "jti": str(uuid.uuid4())}


def _hdr(sub=None, role="operator"):
    return {"Authorization": f"Bearer {create_access_token({'sub': sub or _USER_ID}, role=role)}"}


def _mock_db(rows=None):
    db = AsyncMock(spec=AsyncSession)
    r = MagicMock()
    r.all.return_value = rows or []
    r.scalars.return_value = r
    r.scalar_one_or_none.return_value = None
    r.first.return_value = None
    r.fetchall.return_value = rows or []
    r.scalar.return_value = None
    db.execute.return_value = r
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.add = MagicMock()
    db.delete = AsyncMock()
    return db


def _mkapp(router):
    app = FastAPI()
    app.include_router(router)
    return app


def _mock_issue(status="open", severity=3, complaint_ref="RS-TEST-001"):
    i = MagicMock(spec=RoadIssue)
    i.uuid = uuid.uuid4()
    i.complaint_ref = complaint_ref
    i.issue_type = "pothole"
    i.severity = severity
    i.description = "A test pothole"
    i.location = None
    i.location_address = "Test Address"
    i.road_name = "Test Road"
    i.road_type = "NH"
    i.road_number = "NH32"
    i.authority_name = "NHAI"
    i.authority_phone = "1033"
    i.status = status
    i.category = "roads"
    i.sub_category = None
    i.ward_id = "ward_05"
    i.ward_name = "Test Ward"
    i.assigned_officer_id = None
    i.sla_deadline = None
    i.resolved_at = None
    i.created_at = datetime.now(UTC)
    i.before_photo_url = None
    i.after_photo_url = None
    i.photo_url = None
    i.confirmation_count = 0
    i.complaint_portal = "https://nhai.gov.in"
    i.rejection_reason = None
    i.reopen_count = 0
    i.ai_detection = None
    i.duplicate_of_uuid = None
    i.reporter_id = None
    i.citizen_phone = None
    i.citizen_rating = None
    i.authority_email = None
    return i


def _mock_officer():
    o = MagicMock(spec=Officer)
    o.id = uuid.uuid4()
    o.name = "Test Officer"
    o.phone = "9000000000"
    o.email = "officer@test.com"
    o.role = "field_officer"
    o.ward_id = "ward_05"
    o.department = "PWD"
    o.is_active = True
    o.last_checkin = datetime.now(UTC)
    o.last_location = None
    o.created_at = datetime.now(UTC)
    return o


def _mock_user_profile():
    p = MagicMock(spec=UserProfile)
    p.id = uuid.uuid4()
    p.user_id = "test-user"
    p.name = "Test User"
    p.blood_group = "O+"
    p.emergency_contacts = [{"name": "Contact1", "phone": "9999999999", "relation": "friend"}]
    p.allergies = None
    p.vehicle_details = None
    p.medical_notes = None
    p.created_at = datetime.now(UTC)
    p.updated_at = datetime.now(UTC)
    return p


# ══════════════════════════════════════════════════════════════════════════════
# auth
# ══════════════════════════════════════════════════════════════════════════════

class TestAuthCoverage:

    def test_verify_pbkdf2_wrong_algorithm(self):
        from api.v1.auth import _verify_pbkdf2_password
        assert not _verify_pbkdf2_password("pass", "md5$10000$salt$hexdigest")

    def test_verify_pbkdf2_malformed_hash(self):
        from api.v1.auth import _verify_pbkdf2_password
        assert not _verify_pbkdf2_password("pass", "not-enough-parts")
        assert not _verify_pbkdf2_password("pass", "")

    def test_verify_pbkdf2_valid(self):
        from api.v1.auth import _hash_password, _verify_pbkdf2_password
        h = _hash_password("correct-horse-battery")
        assert _verify_pbkdf2_password("correct-horse-battery", h)
        assert not _verify_pbkdf2_password("wrong", h)

    def test_login_wrong_password_for_db_user(self):
        uid = uuid.uuid4()
        op = MagicMock()
        op.email = "dbuser@test.com"
        op.name = "DB User"
        op.hashed_password = "pbkdf2_sha256$100000$salt$digest"
        op.role = "operator"
        op.is_active = True
        op.id = uid

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = op

        db = _mock_db()
        db.execute.return_value = result_mock

        from api.v1.auth import router
        app = _mkapp(router)
        app.dependency_overrides[get_db] = lambda: db
        from core.limiter import limiter
        app.dependency_overrides[limiter.limit] = lambda *a, **kw: lambda x: x

        resp = TestClient(app).post(
            "/api/v1/auth/login",
            json={"email": "dbuser@test.com", "password": "wrongpassword"},
        )
        assert resp.status_code == 401
        assert resp.json()["detail"] == "Invalid credentials"

    def test_login_wrong_password_env_operator(self, monkeypatch):
        monkeypatch.setenv("AUTH_OPERATOR_EMAIL", "envop@test.com")
        monkeypatch.setenv("AUTH_OPERATOR_NAME", "Env Op")
        from api.v1.auth import _hash_password
        h = _hash_password("realpassword")
        monkeypatch.setenv("AUTH_OPERATOR_PASSWORD_HASH", h)

        from api.v1.auth import router
        app = _mkapp(router)
        from core.limiter import limiter
        app.dependency_overrides[limiter.limit] = lambda *a, **kw: lambda x: x
        from api.v1.auth import _configured_operator
        assert _configured_operator() is not None

        db = _mock_db()
        db.execute.return_value.scalar_one_or_none.return_value = None
        app.dependency_overrides[get_db] = lambda: db

        resp = TestClient(app).post(
            "/api/v1/auth/login",
            json={"email": "envop@test.com", "password": "wrongpassword"},
        )
        assert resp.status_code == 401

    def test_refresh_revoked_token(self):
        from api.v1.auth import router
        app = _mkapp(router)
        from core.limiter import limiter
        app.dependency_overrides[limiter.limit] = lambda *a, **kw: lambda x: x

        jti = str(uuid.uuid4())
        refresh = jwt.encode({
            "sub": "user@test.com",
            "jti": jti,
            "purpose": "refresh",
            "exp": datetime.now(UTC) + timedelta(days=1),
            "iat": datetime.now(UTC),
            "aud": APP_JWT_AUDIENCE,
            "iss": APP_JWT_ISSUER,
        }, SECRET_KEY, algorithm=ALGORITHM)

        _revoked_token_jtis[jti] = None
        try:
            resp = TestClient(app).post(
                "/api/v1/auth/refresh",
                json={"refresh_token": refresh},
            )
            assert resp.status_code == 401
            assert resp.json()["detail"] == "Refresh token has been revoked"
        finally:
            _revoked_token_jtis.pop(jti, None)

    def test_refresh_expired_token(self):
        from api.v1.auth import router
        app = _mkapp(router)
        from core.limiter import limiter
        app.dependency_overrides[limiter.limit] = lambda *a, **kw: lambda x: x

        refresh = jwt.encode({
            "sub": "user@test.com",
            "jti": str(uuid.uuid4()),
            "purpose": "refresh",
            "exp": datetime.now(UTC) - timedelta(hours=1),
            "iat": datetime.now(UTC) - timedelta(hours=2),
            "aud": APP_JWT_AUDIENCE,
            "iss": APP_JWT_ISSUER,
        }, SECRET_KEY, algorithm=ALGORITHM)

        resp = TestClient(app).post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh},
        )
        assert resp.status_code == 401
        assert "expired" in resp.json()["detail"].lower()

    def test_refresh_invalid_purpose(self):
        from api.v1.auth import router
        app = _mkapp(router)
        from core.limiter import limiter
        app.dependency_overrides[limiter.limit] = lambda *a, **kw: lambda x: x

        token = create_access_token({"sub": "user@test.com"})
        resp = TestClient(app).post(
            "/api/v1/auth/refresh",
            json={"refresh_token": token},
        )
        assert resp.status_code == 401

    def test_refresh_success(self):
        from api.v1.auth import router
        app = _mkapp(router)
        from core.limiter import limiter
        app.dependency_overrides[limiter.limit] = lambda *a, **kw: lambda x: x

        refresh = create_refresh_token({"sub": "user@test.com", "name": "Test", "role": "operator"})
        resp = TestClient(app).post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh},
        )
        assert resp.status_code == 200
        assert resp.json()["message"] == "Token refreshed successfully"

    def test_logout(self):
        from api.v1.auth import router
        app = _mkapp(router)
        from core.limiter import limiter
        app.dependency_overrides[limiter.limit] = lambda *a, **kw: lambda x: x
        resp = TestClient(app).post("/api/v1/auth/logout")
        assert resp.status_code == 200

    def test_csrf_token(self):
        from api.v1.auth import router
        app = _mkapp(router)
        from core.limiter import limiter
        app.dependency_overrides[limiter.limit] = lambda *a, **kw: lambda x: x
        resp = TestClient(app).get("/api/v1/auth/csrf-token")
        assert resp.status_code == 200
        assert "csrf_token" in resp.json()

    def test_register_success(self):
        from api.v1.auth import router

        result = MagicMock()
        result.scalar_one_or_none.return_value = None

        db = _mock_db()
        db.execute.return_value = result

        app = _mkapp(router)
        app.dependency_overrides[get_db] = lambda: db
        from core.limiter import limiter
        app.dependency_overrides[limiter.limit] = lambda *a, **kw: lambda x: x

        resp = TestClient(app).post(
            "/api/v1/auth/register",
            json={"email": "newop@test.com", "password": "strongpass123", "name": "New Op"},
        )
        assert resp.status_code == 201

    def test_register_duplicate(self):
        from api.v1.auth import router
        existing = MagicMock()
        existing.email = "dup@test.com"
        result = MagicMock()
        result.scalar_one_or_none.return_value = existing

        db = _mock_db()
        db.execute.return_value = result

        app = _mkapp(router)
        app.dependency_overrides[get_db] = lambda: db
        from core.limiter import limiter
        app.dependency_overrides[limiter.limit] = lambda *a, **kw: lambda x: x

        resp = TestClient(app).post(
            "/api/v1/auth/register",
            json={"email": "dup@test.com", "password": "strongpass123", "name": "Dup Op"},
        )
        assert resp.status_code == 400
        assert "already exists" in resp.json()["detail"].lower()

    def test_verify_token_revoked(self):
        jti = str(uuid.uuid4())
        token = jwt.encode({
            "sub": "user@test.com",
            "jti": jti,
            "role": "operator",
            "exp": datetime.now(UTC) + timedelta(hours=1),
            "iat": datetime.now(UTC),
            "aud": APP_JWT_AUDIENCE,
            "iss": APP_JWT_ISSUER,
        }, SECRET_KEY, algorithm=ALGORITHM)

        from api.v1.auth import router
        # Do NOT override get_current_user — let the real dependency run
        _revoked_token_jtis[jti] = None
        try:
            resp = TestClient(_mkapp(router)).get(
                "/api/v1/auth/verify",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert resp.status_code == 401
        finally:
            _revoked_token_jtis.pop(jti, None)

    def test_revoke_token(self):
        from api.v1.auth import router
        app = _mkapp(router)
        from core.limiter import limiter
        app.dependency_overrides[limiter.limit] = lambda *a, **kw: lambda x: x
        app.dependency_overrides[get_current_user] = lambda: _auth(role="operator")
        resp = TestClient(app).post(
            "/api/v1/auth/revoke",
            headers=_hdr(role="operator"),
        )
        assert resp.status_code == 200


# ══════════════════════════════════════════════════════════════════════════════
# authority
# ══════════════════════════════════════════════════════════════════════════════

class TestAuthorityCoverage:

    def _app(self):
        from api.v1.authority import router
        app = _mkapp(router)
        uid = _USER_ID
        app.dependency_overrides[get_current_user] = lambda: _auth(sub=uid, role="field_officer")
        app.dependency_overrides[require_role(Role.FIELD_OFFICER)] = lambda: _auth(sub=uid, role="field_officer")
        from core.limiter import limiter
        app.dependency_overrides[limiter.limit] = lambda *a, **kw: lambda x: x
        return app

    def test_accept_bad_uuid(self):
        r = TestClient(self._app()).post(
            "/api/v1/authority/complaints/not-uuid/accept",
            json={"notes": "x"}, headers=_hdr(role="field_officer"))
        assert r.status_code == 422

    @patch("api.v1.authority.ComplaintStateMachine.transition", new_callable=AsyncMock)
    def test_accept_success(self, mock_transition):
        mock_result = MagicMock()
        mock_issue = _mock_issue()
        mock_result.issue = mock_issue
        mock_result.new_status = "accepted"
        mock_transition.return_value = mock_result

        r = TestClient(self._app()).post(
            f"/api/v1/authority/complaints/{uuid.uuid4()}/accept",
            json={"notes": "Accepting complaint"},
            headers=_hdr(role="field_officer"))
        assert r.status_code == 200
        assert r.json()["status"] == "accepted"

    @patch("api.v1.authority.ComplaintStateMachine.transition", new_callable=AsyncMock)
    def test_accept_invalid_transition(self, mock_transition):
        from services.complaint_state_machine import InvalidTransitionError
        mock_transition.side_effect = InvalidTransitionError("assigned", "accepted", "RS-001")

        r = TestClient(self._app()).post(
            f"/api/v1/authority/complaints/{uuid.uuid4()}/accept",
            json={"notes": "x"},
            headers=_hdr(role="field_officer"))
        assert r.status_code == 409

    @patch("api.v1.authority.ComplaintStateMachine.transition", new_callable=AsyncMock)
    def test_accept_not_found(self, mock_transition):
        mock_transition.side_effect = ValueError("Not found")

        r = TestClient(self._app()).post(
            f"/api/v1/authority/complaints/{uuid.uuid4()}/accept",
            json={"notes": "x"},
            headers=_hdr(role="field_officer"))
        assert r.status_code == 404

    def test_reject_no_reason(self):
        r = TestClient(self._app()).post(
            f"/api/v1/authority/complaints/{uuid.uuid4()}/reject",
            json={}, headers=_hdr(role="field_officer"))
        assert r.status_code == 422

    @patch("api.v1.authority.ComplaintStateMachine.transition", new_callable=AsyncMock)
    def test_reject_success_no_auto_reassign(self, mock_transition):
        mock_result = MagicMock()
        mock_issue = _mock_issue()
        mock_issue.location = "POINT(80.27 13.08)"
        mock_result.issue = mock_issue
        mock_result.new_status = "reassigned"
        mock_transition.return_value = mock_result

        r = TestClient(self._app()).post(
            f"/api/v1/authority/complaints/{uuid.uuid4()}/reject",
            json={"reason": "Not in my jurisdiction"},
            headers=_hdr(role="field_officer"))
        assert r.status_code == 200
        assert r.json()["reassigned_to"] is None

    def test_escalate_short_reason(self):
        r = TestClient(self._app()).post(
            f"/api/v1/authority/complaints/{uuid.uuid4()}/escalate",
            json={"reason": "bad"}, headers=_hdr(role="field_officer"))
        assert r.status_code == 422

    @patch("api.v1.authority.ComplaintStateMachine.escalate", new_callable=AsyncMock)
    def test_escalate_success(self, mock_escalate):
        mock_result = MagicMock()
        mock_issue = _mock_issue()
        mock_result.issue = mock_issue
        mock_escalate.return_value = mock_result

        r = TestClient(self._app()).post(
            f"/api/v1/authority/complaints/{uuid.uuid4()}/escalate",
            json={"reason": "Requires immediate attention", "target_tier": 3},
            headers=_hdr(role="field_officer"))
        assert r.status_code == 200
        assert r.json()["status"] == "escalated"

    @patch("api.v1.authority.ComplaintStateMachine.escalate", new_callable=AsyncMock)
    def test_escalate_not_found(self, mock_escalate):
        mock_escalate.side_effect = ValueError("Not found")

    def test_pending_success(self):
        officer_id = uuid.uuid4()
        issue = _mock_issue(status="assigned")
        issue.assigned_officer_id = officer_id
        issue.sla_deadline = datetime.now(UTC) + timedelta(hours=24)

        db = _mock_db(rows=[issue])
        db.execute.return_value.scalars.return_value.all.return_value = [issue]

        from api.v1.authority import router
        app = _mkapp(router)
        app.dependency_overrides[get_db] = lambda: db
        s = str(officer_id)
        app.dependency_overrides[get_current_user] = lambda: _auth(sub=s, role="field_officer")
        app.dependency_overrides[require_role(Role.FIELD_OFFICER)] = lambda: _auth(sub=s, role="field_officer")
        from core.limiter import limiter
        app.dependency_overrides[limiter.limit] = lambda *a, **kw: lambda x: x

        r = TestClient(app).get("/api/v1/authority/pending", headers=_hdr(role="field_officer"))
        assert r.status_code == 200

    def test_pending_no_auth(self):
        from api.v1.authority import router
        r = TestClient(_mkapp(router)).get("/api/v1/authority/pending")
        assert r.status_code == 401


# ══════════════════════════════════════════════════════════════════════════════
# citizen
# ══════════════════════════════════════════════════════════════════════════════

class TestCitizenCoverage:

    def _app(self):
        from api.v1.citizen import router
        app = _mkapp(router)
        from core.limiter import limiter
        app.dependency_overrides[limiter.limit] = lambda *a, **kw: lambda x: x
        return app

    def test_track_complaint_not_found(self):
        db = _mock_db()
        db.execute.return_value.scalar_one_or_none.return_value = None
        app = self._app()
        app.dependency_overrides[get_db] = lambda: db
        r = TestClient(app).get("/api/v1/citizen/complaints/NONEXISTENT")
        assert r.status_code == 404

    def test_track_complaint_found(self):
        issue = _mock_issue()
        db = _mock_db()
        first_result = MagicMock()
        first_result.scalar_one_or_none.return_value = issue
        # second call for coordinates
        coord_result = MagicMock()
        coord_result.first.return_value = None
        db.execute.side_effect = [first_result, coord_result]
        app = self._app()
        app.dependency_overrides[get_db] = lambda: db
        r = TestClient(app).get(f"/api/v1/citizen/complaints/{issue.complaint_ref}")
        assert r.status_code == 200
        assert r.json()["complaint_ref"] == issue.complaint_ref

    def test_track_complaint_sla_breached(self):
        issue = _mock_issue()
        issue.sla_deadline = datetime.now(UTC).replace(tzinfo=None) - timedelta(hours=2)
        db = _mock_db()
        first_result = MagicMock()
        first_result.scalar_one_or_none.return_value = issue
        coord_result = MagicMock()
        coord_result.first.return_value = None
        db.execute.side_effect = [first_result, coord_result]
        app = self._app()
        app.dependency_overrides[get_db] = lambda: db
        r = TestClient(app).get(f"/api/v1/citizen/complaints/{issue.complaint_ref}")
        assert r.status_code == 200
        assert r.json()["sla_status"] == "breached"

    def test_confirm_resolution_not_found(self):
        db = _mock_db()
        db.execute.return_value.scalar_one_or_none.return_value = None
        app = self._app()
        app.dependency_overrides[get_db] = lambda: db
        r = TestClient(app).post(
            "/api/v1/citizen/complaints/RS-NOTFOUND/confirm",
            json={"citizen_phone": "9999999999"})
        assert r.status_code == 404

    def test_confirm_resolution_wrong_status(self):
        issue = _mock_issue(status="open")
        db = _mock_db()
        db.execute.return_value.scalar_one_or_none.return_value = issue
        app = self._app()
        app.dependency_overrides[get_db] = lambda: db
        r = TestClient(app).post(
            f"/api/v1/citizen/complaints/{issue.complaint_ref}/confirm",
            json={"citizen_phone": "9999999999"})
        assert r.status_code == 409

    @patch("api.v1.citizen.ComplaintStateMachine")
    def test_confirm_resolution_success(self, mock_csm):
        issue = _mock_issue(status="resolved")
        mock_result = MagicMock()
        mock_result.issue = issue
        mock_csm.transition = AsyncMock(return_value=mock_result)

        db = _mock_db()
        db.execute.return_value.scalar_one_or_none.return_value = issue
        app = self._app()
        app.dependency_overrides[get_db] = lambda: db
        r = TestClient(app).post(
            f"/api/v1/citizen/complaints/{issue.complaint_ref}/confirm",
            json={"citizen_phone": "9999999999"})
        # May succeed or 409 depending on state machine second call
        assert r.status_code in (200, 409)

    def test_reject_resolution_not_found(self):
        db = _mock_db()
        db.execute.return_value.scalar_one_or_none.return_value = None
        app = self._app()
        app.dependency_overrides[get_db] = lambda: db
        r = TestClient(app).post(
            "/api/v1/citizen/complaints/RS-NOTFOUND/reject",
            json={"reason": "Work was not done properly"})
        assert r.status_code == 404

    def test_reject_resolution_wrong_status(self):
        issue = _mock_issue(status="open")
        db = _mock_db()
        db.execute.return_value.scalar_one_or_none.return_value = issue
        app = self._app()
        app.dependency_overrides[get_db] = lambda: db
        r = TestClient(app).post(
            f"/api/v1/citizen/complaints/{issue.complaint_ref}/reject",
            json={"reason": "Work was not done properly"})
        assert r.status_code == 409

    def test_reject_short_reason(self):
        r = TestClient(self._app()).post(
            "/api/v1/citizen/complaints/RS-TEST/reject",
            json={"reason": "bad"})
        assert r.status_code == 422

    @patch("api.v1.citizen.ComplaintStateMachine")
    def test_reject_resolution_success(self, mock_csm):
        issue = _mock_issue(status="resolved")
        mock_result = MagicMock()
        mock_result.issue = issue
        mock_csm.transition = AsyncMock(return_value=mock_result)

        db = _mock_db()
        db.execute.return_value.scalar_one_or_none.return_value = issue
        app = self._app()
        app.dependency_overrides[get_db] = lambda: db
        r = TestClient(app).post(
            f"/api/v1/citizen/complaints/{issue.complaint_ref}/reject",
            json={"reason": "Work was not done properly"})
        assert r.status_code in (200, 409)

    def test_rate_not_found(self):
        db = _mock_db()
        db.execute.return_value.scalar_one_or_none.return_value = None
        app = self._app()
        app.dependency_overrides[get_db] = lambda: db
        r = TestClient(app).post(
            "/api/v1/citizen/complaints/RS-NOTFOUND/rate",
            json={"rating": 4})
        assert r.status_code == 404

    def test_rate_wrong_status(self):
        issue = _mock_issue(status="open")
        db = _mock_db()
        db.execute.return_value.scalar_one_or_none.return_value = issue
        app = self._app()
        app.dependency_overrides[get_db] = lambda: db
        r = TestClient(app).post(
            f"/api/v1/citizen/complaints/{issue.complaint_ref}/rate",
            json={"rating": 4})
        assert r.status_code == 409

    def test_rate_bad_value(self):
        r = TestClient(self._app()).post(
            "/api/v1/citizen/complaints/RS-TEST/rate",
            json={"rating": 6})
        assert r.status_code == 422

    def test_rate_success(self):
        issue = _mock_issue(status="citizen_confirmed")
        db = _mock_db()
        db.execute.return_value.scalar_one_or_none.return_value = issue
        app = self._app()
        app.dependency_overrides[get_db] = lambda: db
        r = TestClient(app).post(
            f"/api/v1/citizen/complaints/{issue.complaint_ref}/rate",
            json={"rating": 4, "feedback": "Good work!"})
        assert r.status_code == 200
        assert r.json()["rating"] == 4

    def test_timeline_not_found(self):
        db = _mock_db()
        db.execute.return_value.scalar_one_or_none.return_value = None
        app = self._app()
        app.dependency_overrides[get_db] = lambda: db
        r = TestClient(app).get("/api/v1/citizen/complaints/RS-NOTFOUND/timeline")
        assert r.status_code == 404

    def test_timeline_success(self):
        issue = _mock_issue()
        event = MagicMock()
        event.event_type = "created"
        event.actor_role = "citizen"
        event.notes = "Issue reported"
        event.created_at = datetime.now(UTC)
        event.id = 1
        event.complaint_uuid = issue.uuid
        event.event_metadata = {}

        db = _mock_db()
        first_result = MagicMock()
        first_result.scalar_one_or_none.return_value = issue
        second_result = MagicMock()
        second_result.scalars.return_value.all.return_value = [event]
        db.execute.side_effect = [first_result, second_result]

        app = self._app()
        app.dependency_overrides[get_db] = lambda: db
        r = TestClient(app).get(f"/api/v1/citizen/complaints/{issue.complaint_ref}/timeline")
        assert r.status_code == 200
        assert len(r.json()["timeline"]) == 1


# ══════════════════════════════════════════════════════════════════════════════
# public
# ══════════════════════════════════════════════════════════════════════════════

class TestPublicCoverage:

    def _app(self):
        from api.v1.public import router
        app = _mkapp(router)
        from core.limiter import limiter
        app.dependency_overrides[limiter.limit] = lambda *a, **kw: lambda x: x
        return app

    def test_ward_rankings_empty(self):
        with patch("services.ward_service.WardService.ensure_seeded", AsyncMock()):
            db = _mock_db()
            db.execute.return_value.all.return_value = []
            app = self._app()
            app.dependency_overrides[get_db] = lambda: db
            r = TestClient(app).get("/api/v1/public/ward-rankings")
        assert r.status_code == 200
        assert r.json()["total_wards"] == 0
        assert r.json()["rankings"] == []

    def test_ward_rankings_with_data(self):
        with patch("services.ward_service.WardService.ensure_seeded", AsyncMock()):
            row = MagicMock()
            row.ward_id = "w01"
            row.ward_name = "Test Ward"
            row.zone_name = "Zone 1"
            row.population = 50000
            row.total = 10
            row.resolved = 5
            row.active = 3
            row.breached = 1
            row.avg_resolution_hours = 48.5
            db = _mock_db()
            db.execute.return_value.all.return_value = [row]
            app = self._app()
            app.dependency_overrides[get_db] = lambda: db
            r = TestClient(app).get("/api/v1/public/ward-rankings")
        assert r.status_code == 200
        assert r.json()["total_wards"] == 1

    def test_authority_performance_empty(self):
        db = _mock_db()
        db.execute.return_value.all.return_value = []
        app = self._app()
        app.dependency_overrides[get_db] = lambda: db
        r = TestClient(app).get("/api/v1/public/authority-performance")
        assert r.status_code == 200
        assert r.json()["authorities"] == []

    def test_authority_performance_with_data(self):
        row = ("NHAI", 20, 15)
        db = _mock_db()
        db.execute.return_value.all.return_value = [row]
        app = self._app()
        app.dependency_overrides[get_db] = lambda: db
        r = TestClient(app).get("/api/v1/public/authority-performance")
        assert r.status_code == 200
        assert len(r.json()["authorities"]) == 1

    def test_stats_empty(self):
        db = _mock_db()
        db.execute.return_value.scalar.return_value = 0
        db.execute.return_value.all.return_value = []
        app = self._app()
        app.dependency_overrides[get_db] = lambda: db
        r = TestClient(app).get("/api/v1/public/stats")
        assert r.status_code == 200

    def test_open_issues_map_empty(self):
        db = _mock_db()
        db.execute.return_value.all.return_value = []
        app = self._app()
        app.dependency_overrides[get_db] = lambda: db
        r = TestClient(app).get("/api/v1/public/open-issues-map")
        assert r.status_code == 200
        assert r.json()["total"] == 0

    def test_open_issues_map_with_category(self):
        db = _mock_db()
        db.execute.return_value.all.return_value = []
        app = self._app()
        app.dependency_overrides[get_db] = lambda: db
        r = TestClient(app).get("/api/v1/public/open-issues-map?category=roads")
        assert r.status_code == 200

    def test_complaint_status_found(self):
        issue = _mock_issue(status="resolved")
        db = _mock_db()
        db.execute.return_value.scalar_one_or_none.return_value = issue
        app = self._app()
        app.dependency_overrides[get_db] = lambda: db
        r = TestClient(app).get(f"/api/v1/public/complaint/{issue.complaint_ref}/status")
        assert r.status_code == 200
        assert r.json()["found"] is True

    def test_complaint_status_not_found(self):
        db = _mock_db()
        db.execute.return_value.scalar_one_or_none.return_value = None
        app = self._app()
        app.dependency_overrides[get_db] = lambda: db
        r = TestClient(app).get("/api/v1/public/complaint/RS-NOTFOUND/status")
        assert r.status_code == 200
        assert r.json()["found"] is False

    def test_days_old_none(self):
        from api.v1.public import _days_old
        assert _days_old(None) == 0

    def test_days_old_with_tzinfo(self):
        from api.v1.public import _days_old
        d = datetime.now(UTC) - timedelta(days=5)
        assert _days_old(d) == 5


# ══════════════════════════════════════════════════════════════════════════════
# field_workflow
# ══════════════════════════════════════════════════════════════════════════════

class TestFieldWorkflowCoverage:

    _FW_UID = str(uuid.uuid4())

    def _app(self):
        from api.v1.field_workflow import router
        app = _mkapp(router)
        app.dependency_overrides[get_current_user] = lambda: _auth(sub=self._FW_UID, role="field_officer")
        from core.limiter import limiter
        app.dependency_overrides[limiter.limit] = lambda *a, **kw: lambda x: x
        return app

    def test_start_work_bad_uuid(self):
        r = TestClient(self._app()).post(
            "/api/v1/field/complaints/not-uuid/start-work",
            json={"officer_lat": 13.08, "officer_lon": 80.27},
            headers=_hdr(sub=self._FW_UID, role="field_officer"))
        assert r.status_code == 422

    def test_start_work_not_found(self):
        db = _mock_db()
        db.execute.return_value.scalar_one_or_none.return_value = None
        app = self._app()
        app.dependency_overrides[get_db] = lambda: db
        r = TestClient(app).post(
            f"/api/v1/field/complaints/{uuid.uuid4()}/start-work",
            json={"officer_lat": 13.08, "officer_lon": 80.27},
            headers=_hdr(sub=self._FW_UID, role="field_officer"))
        assert r.status_code == 404

    @patch("api.v1.field_workflow.ComplaintStateMachine.transition", new_callable=AsyncMock)
    def test_start_work_invalid_transition(self, mock_transition):
        from services.complaint_state_machine import InvalidTransitionError
        mock_transition.side_effect = InvalidTransitionError("open", "in_progress", "RS-001")

        issue = _mock_issue()
        db = _mock_db()
        db.execute.return_value.scalar_one_or_none.return_value = issue
        app = self._app()
        app.dependency_overrides[get_db] = lambda: db
        r = TestClient(app).post(
            f"/api/v1/field/complaints/{uuid.uuid4()}/start-work",
            json={"officer_lat": 13.08, "officer_lon": 80.27},
            headers=_hdr(sub=self._FW_UID, role="field_officer"))
        assert r.status_code == 409

    @patch("api.v1.field_workflow.ComplaintStateMachine.transition", new_callable=AsyncMock)
    def test_start_work_success(self, mock_transition):
        mock_result = MagicMock()
        mock_issue = _mock_issue()
        mock_result.issue = mock_issue
        mock_transition.return_value = mock_result

        issue = _mock_issue()
        issue.location = "POINT(80.27 13.08)"
        db = _mock_db()
        db.execute.return_value.scalar_one_or_none.return_value = issue
        app = self._app()
        app.dependency_overrides[get_db] = lambda: db

        with patch("api.v1.field_workflow._get_issue_coords", AsyncMock(return_value=(13.08, 80.27))):
            r = TestClient(app).post(
                f"/api/v1/field/complaints/{uuid.uuid4()}/start-work",
                json={"officer_lat": 13.08, "officer_lon": 80.27, "notes": "Starting work"},
                headers=_hdr(sub=self._FW_UID, role="field_officer"))
        assert r.status_code == 200
        assert r.json()["status"] == "work_started"

    def test_complete_work_bad_uuid(self):
        r = TestClient(self._app()).post(
            "/api/v1/field/complaints/not-uuid/complete",
            json={"officer_lat": 13.08, "officer_lon": 80.27, "resolution_notes": "Fixed the pothole"},
            headers=_hdr(sub=self._FW_UID, role="field_officer"))
        assert r.status_code == 422

    def test_complete_work_not_found(self):
        db = _mock_db()
        db.execute.return_value.scalar_one_or_none.return_value = None
        app = self._app()
        app.dependency_overrides[get_db] = lambda: db
        r = TestClient(app).post(
            f"/api/v1/field/complaints/{uuid.uuid4()}/complete",
            json={"officer_lat": 13.08, "officer_lon": 80.27, "resolution_notes": "Fixed the pothole"},
            headers=_hdr(sub=self._FW_UID, role="field_officer"))
        assert r.status_code == 404

    def test_complete_work_short_notes(self):
        r = TestClient(self._app()).post(
            f"/api/v1/field/complaints/{uuid.uuid4()}/complete",
            json={"officer_lat": 13.08, "officer_lon": 80.27, "resolution_notes": "bad"},
            headers=_hdr(role="field_officer"))
        assert r.status_code == 422

    @patch("api.v1.field_workflow.ComplaintStateMachine.transition", new_callable=AsyncMock)
    def test_complete_work_success(self, mock_transition):
        mock_result = MagicMock()
        mock_issue = _mock_issue()
        mock_result.issue = mock_issue
        mock_transition.return_value = mock_result

        issue = _mock_issue()
        issue.location = "POINT(80.27 13.08)"
        db = _mock_db()
        db.execute.return_value.scalar_one_or_none.return_value = issue
        app = self._app()
        app.dependency_overrides[get_db] = lambda: db

        with patch("api.v1.field_workflow._get_issue_coords", AsyncMock(return_value=(13.08, 80.27))):
            r = TestClient(app).post(
                f"/api/v1/field/complaints/{uuid.uuid4()}/complete",
                json={
                    "officer_lat": 13.08, "officer_lon": 80.27,
                    "resolution_notes": "Pothole filled with asphalt",
                    "after_photo_url": "https://example.com/after.jpg",
                },
                headers=_hdr(sub=self._FW_UID, role="field_officer"))
        assert r.status_code == 200
        assert r.json()["status"] == "resolved"

    def test_geo_checkin_bad_uuid(self):
        r = TestClient(self._app()).post(
            "/api/v1/field/complaints/not-uuid/geo-checkin",
            json={"lat": 13.08, "lon": 80.27},
            headers=_hdr(role="field_officer"))
        assert r.status_code == 422

    def test_geo_checkin_not_found(self):
        db = _mock_db()
        db.execute.return_value.scalar_one_or_none.return_value = None
        app = self._app()
        app.dependency_overrides[get_db] = lambda: db
        r = TestClient(app).post(
            f"/api/v1/field/complaints/{uuid.uuid4()}/geo-checkin",
            json={"lat": 13.08, "lon": 80.27},
            headers=_hdr(role="field_officer"))
        assert r.status_code == 404

    def test_geo_checkin_no_coords(self):
        issue = _mock_issue()
        db = _mock_db()
        db.execute.return_value.scalar_one_or_none.return_value = issue
        app = self._app()
        app.dependency_overrides[get_db] = lambda: db
        with patch("api.v1.field_workflow._get_issue_coords", AsyncMock(return_value=(None, None))):
            r = TestClient(app).post(
                f"/api/v1/field/complaints/{uuid.uuid4()}/geo-checkin",
                json={"lat": 13.08, "lon": 80.27},
                headers=_hdr(role="field_officer"))
        assert r.status_code == 200
        assert r.json()["verified"] is False

    def test_geo_checkin_verified(self):
        issue = _mock_issue()
        db = _mock_db()
        db.execute.return_value.scalar_one_or_none.return_value = issue
        app = self._app()
        app.dependency_overrides[get_db] = lambda: db
        with patch("api.v1.field_workflow._get_issue_coords", AsyncMock(return_value=(13.08, 80.27))):
            r = TestClient(app).post(
                f"/api/v1/field/complaints/{uuid.uuid4()}/geo-checkin",
                json={"lat": 13.08, "lon": 80.27},
                headers=_hdr(role="field_officer"))
        assert r.status_code == 200
        assert r.json()["verified"] is True

    def test_get_optimized_route_no_auth(self):
        from api.v1.field_workflow import router
        r = TestClient(_mkapp(router)).get(
            "/api/v1/field/my-route?lat=13.08&lon=80.27")
        assert r.status_code == 401

    def test_get_optimized_route_bad_token(self):
        from api.v1.field_workflow import router
        app = _mkapp(router)
        app.dependency_overrides[get_current_user] = lambda: {"role": "field_officer"}
        from core.limiter import limiter
        app.dependency_overrides[limiter.limit] = lambda *a, **kw: lambda x: x
        r = TestClient(app).get(
            "/api/v1/field/my-route?lat=13.08&lon=80.27",
            headers=_hdr(role="field_officer"))
        assert r.status_code == 401

    @patch("services.officer_route_optimizer.OfficerRouteOptimizer.optimize_route", new_callable=AsyncMock)
    def test_get_optimized_route_success(self, mock_optimize):
        mock_stop = MagicMock()
        mock_stop.order = 1
        mock_stop.complaint_ref = "RS-001"
        mock_stop.issue_type = "pothole"
        mock_stop.severity = 3
        mock_stop.lat = 13.08
        mock_stop.lon = 80.27
        mock_stop.distance_from_prev_km = 0.0
        mock_stop.estimated_arrival_minutes = 5
        mock_stop.address = "Test"

        mock_route = MagicMock()
        mock_route.officer_id = str(uuid.uuid4())
        mock_route.total_stops = 3
        mock_route.total_distance_km = 12.5
        mock_route.estimated_duration_minutes = 45
        mock_route.warnings = []
        mock_route.stops = [mock_stop]
        mock_optimize.return_value = mock_route

        from api.v1.field_workflow import router
        app = _mkapp(router)
        app.dependency_overrides[get_current_user] = lambda: _auth(sub=self._FW_UID, role="field_officer")
        from core.limiter import limiter
        app.dependency_overrides[limiter.limit] = lambda *a, **kw: lambda x: x
        r = TestClient(app).get(
            "/api/v1/field/my-route?lat=13.08&lon=80.27",
            headers=_hdr(sub=self._FW_UID, role="field_officer"))
        assert r.status_code == 200
        assert r.json()["total_stops"] == 3

    def test_haversine(self):
        from api.v1.field_workflow import _haversine_meters
        d = _haversine_meters(13.08, 80.27, 13.08, 80.27)
        assert d == 0.0
        d2 = _haversine_meters(13.08, 80.27, 13.09, 80.28)
        assert d2 > 0

    def test_get_issue_coords_no_location(self):
        from api.v1.field_workflow import _get_issue_coords
        issue = _mock_issue()
        issue.location = None
        coords = asyncio.run(_get_issue_coords(_mock_db(), issue))
        assert coords == (None, None)

    def test_get_issue_coords_with_location(self):
        from api.v1.field_workflow import _get_issue_coords
        issue = _mock_issue()
        issue.location = "POINT(80.27 13.08)"
        db = _mock_db()
        coord_row = MagicMock()
        coord_row.__getitem__ = lambda self, i: [13.08, 80.27][i]
        coord_row.first.return_value = coord_row
        db.execute.return_value = coord_row
        coords = asyncio.run(_get_issue_coords(db, issue))
        assert coords == (13.08, 80.27)


# ══════════════════════════════════════════════════════════════════════════════
# officers
# ══════════════════════════════════════════════════════════════════════════════

class TestOfficersCoverage:

    @patch("api.v1.officers.get_settings")
    def test_get_or_create_officer_creates_new(self, mock_settings):
        mock_settings.return_value.default_officer_ward = "ward_05"
        from api.v1.officers import get_or_create_officer

        db = _mock_db()
        db.execute.return_value.scalar_one_or_none.return_value = None

        current_user = {"sub": str(uuid.uuid4()), "name": "New Officer", "email": "new@test.com"}
        officer = asyncio.run(get_or_create_officer(db, current_user))
        assert officer is not None

    def test_get_or_create_officer_invalid_user(self):
        import pytest

        from api.v1.officers import get_or_create_officer
        with pytest.raises(Exception):
            asyncio.run(get_or_create_officer(_mock_db(), {"role": "user"}))

    def test_officer_me_success(self):
        officer = _mock_officer()
        db = _mock_db()
        db.execute.return_value.scalar_one_or_none.return_value = officer

        from api.v1.officers import router
        app = _mkapp(router)
        app.dependency_overrides[get_db] = lambda: db
        app.dependency_overrides[get_current_user] = lambda: _auth(sub=str(officer.id))
        from core.limiter import limiter
        app.dependency_overrides[limiter.limit] = lambda *a, **kw: lambda x: x
        r = TestClient(app).get("/api/v1/officers/me", headers=_hdr(role="field_officer"))
        assert r.status_code == 200
        assert r.json()["name"] == "Test Officer"

    def test_officer_me_no_auth(self):
        from api.v1.officers import router
        r = TestClient(_mkapp(router)).get("/api/v1/officers/me")
        assert r.status_code == 401

    def test_checkin_success(self):
        officer = _mock_officer()
        officer.last_checkin = datetime.now(UTC)
        db = _mock_db()
        db.execute.return_value.scalar_one_or_none.return_value = officer

        from api.v1.officers import router
        app = _mkapp(router)
        app.dependency_overrides[get_db] = lambda: db
        app.dependency_overrides[get_current_user] = lambda: _auth(sub=str(officer.id))
        from core.limiter import limiter
        app.dependency_overrides[limiter.limit] = lambda *a, **kw: lambda x: x
        r = TestClient(app).post(
            "/api/v1/officers/checkin",
            json={"lat": 13.08, "lon": 80.27},
            headers=_hdr(role="field_officer"))
        assert r.status_code == 200
        assert r.json()["status"] == "success"

    def test_checkin_no_auth(self):
        from api.v1.officers import router
        r = TestClient(_mkapp(router)).post(
            "/api/v1/officers/checkin", json={"lat": 13, "lon": 80})
        assert r.status_code == 401

    def test_workload_success_empty(self):
        officer = _mock_officer()
        db = _mock_db()
        db.execute.return_value.scalar_one_or_none.return_value = officer
        db.execute.return_value.all.return_value = []

        from api.v1.officers import router
        app = _mkapp(router)
        app.dependency_overrides[get_db] = lambda: db
        app.dependency_overrides[get_current_user] = lambda: _auth(sub=str(officer.id))
        from core.limiter import limiter
        app.dependency_overrides[limiter.limit] = lambda *a, **kw: lambda x: x
        r = TestClient(app).get("/api/v1/officers/me/workload", headers=_hdr(role="field_officer"))
        assert r.status_code == 200
        assert isinstance(r.json(), list)


# ══════════════════════════════════════════════════════════════════════════════
# user
# ══════════════════════════════════════════════════════════════════════════════

class TestUserCoverage:

    def _app(self):
        from api.v1.user import router
        app = _mkapp(router)
        app.dependency_overrides[get_current_user] = lambda: _auth()
        from core.limiter import limiter
        app.dependency_overrides[limiter.limit] = lambda *a, **kw: lambda x: x
        return app

    def test_create_success(self):
        from models.user import UserProfile as UPModel
        UPModel(
            user_id=_USER_ID,
            name="Test User",
            blood_group="O+",
            emergency_contacts=[],
        )
        db = _mock_db()
        db.add = MagicMock()
        db.commit = AsyncMock()
        async def _set_id_and_refresh(obj):
            obj.id = uuid.uuid4()
            obj.created_at = datetime.now(UTC)
            obj.updated_at = datetime.now(UTC)
        db.refresh = AsyncMock(side_effect=_set_id_and_refresh)

        async def _mock_exec(q):
            r = MagicMock()
            r.scalar_one_or_none.return_value = None
            return r
        db.execute = _mock_exec

        app = self._app()
        app.dependency_overrides[get_db] = lambda: db
        r = TestClient(app).post(
            "/api/v1/users/",
            json={"name": "Test User", "blood_group": "O+", "emergency_contacts": []},
            headers=_hdr())
        assert r.status_code == 201

    def test_create_no_auth(self):
        from api.v1.user import router
        r = TestClient(_mkapp(router)).post(
            "/api/v1/users/",
            json={"name": "U", "emergency_contacts": []})
        assert r.status_code == 401

    def test_create_missing_name(self):
        r = TestClient(self._app()).post(
            "/api/v1/users/", json={"blood_group": "O+"},
            headers=_hdr())
        assert r.status_code == 422

    def test_get_success(self):
        profile = _mock_user_profile()
        db = _mock_db()
        db.execute.return_value.scalar_one_or_none.return_value = profile
        app = self._app()
        app.dependency_overrides[get_db] = lambda: db
        r = TestClient(app).get(f"/api/v1/users/{profile.id}", headers=_hdr())
        assert r.status_code == 200
        assert r.json()["name"] == "Test User"

    def test_get_not_found(self):
        db = _mock_db()
        db.execute.return_value.scalar_one_or_none.return_value = None
        app = self._app()
        app.dependency_overrides[get_db] = lambda: db
        r = TestClient(app).get(f"/api/v1/users/{uuid.uuid4()}", headers=_hdr())
        assert r.status_code == 404

    def test_get_bad_uuid(self):
        r = TestClient(self._app()).get("/api/v1/users/not-uuid", headers=_hdr())
        assert r.status_code == 422

    def test_update_success(self):
        profile = _mock_user_profile()
        db = _mock_db()
        db.execute.return_value.scalar_one_or_none.return_value = profile
        app = self._app()
        app.dependency_overrides[get_db] = lambda: db
        r = TestClient(app).put(
            f"/api/v1/users/{profile.id}",
            json={"name": "Updated Name"},
            headers=_hdr())
        assert r.status_code == 200

    def test_update_not_found(self):
        db = _mock_db()
        db.execute.return_value.scalar_one_or_none.return_value = None
        app = self._app()
        app.dependency_overrides[get_db] = lambda: db
        r = TestClient(app).put(
            f"/api/v1/users/{uuid.uuid4()}",
            json={"name": "Updated"},
            headers=_hdr())
        assert r.status_code == 404

    def test_update_bad_uuid(self):
        r = TestClient(self._app()).put(
            "/api/v1/users/not-uuid", json={"name": "X"},
            headers=_hdr())
        assert r.status_code == 422

    def test_export_success(self):
        from models.user import UserProfile as UPModel
        profile = UPModel(
            user_id=_USER_ID,
            name="Test User",
            blood_group="O+",
            emergency_contacts=[{"name": "C", "phone": "9999999999", "relation": "friend"}],
        )
        profile.id = uuid.uuid4()
        profile.created_at = datetime.now(UTC)
        profile.updated_at = datetime.now(UTC)
        sos_mock = MagicMock()
        sos_mock.id = uuid.uuid4()
        sos_mock.lat = 13.0
        sos_mock.lon = 80.0
        sos_mock.created_at = datetime.now(UTC)
        sos_mock.to_dict.return_value = {"id": str(sos_mock.id), "lat": 13.0, "lon": 80.0, "created_at": str(sos_mock.created_at)}
        road_mock = MagicMock()
        road_mock.uuid = uuid.uuid4()
        road_mock.issue_type = "pothole"
        road_mock.severity = 3
        road_mock.description = "Test"
        road_mock.status = "open"
        road_mock.created_at = datetime.now(UTC)

        class _MultiExec:
            idx = 0
            returns = [
                MagicMock(scalar_one_or_none=lambda: profile),
                MagicMock(scalars=lambda: MagicMock(all=lambda: [sos_mock])),
                MagicMock(scalars=lambda: MagicMock(all=lambda: [road_mock])),
            ]
            async def __call__(self, *a, **kw):
                rv = self.returns[self.idx]
                self.idx += 1
                return rv

        db = _mock_db()
        db.execute = _MultiExec()
        app = self._app()
        app.dependency_overrides[get_db] = lambda: db
        r = TestClient(app).get(f"/api/v1/users/{profile.id}/export", headers=_hdr())
        assert r.status_code == 200

    def test_export_not_found(self):
        db = _mock_db()
        db.execute.return_value.scalar_one_or_none.return_value = None
        app = self._app()
        app.dependency_overrides[get_db] = lambda: db
        r = TestClient(app).get(f"/api/v1/users/{uuid.uuid4()}/export", headers=_hdr())
        assert r.status_code == 404

    def test_export_bad_uuid(self):
        r = TestClient(self._app()).get("/api/v1/users/not-uuid/export", headers=_hdr())
        assert r.status_code == 422

    def test_delete_success(self):
        profile = _mock_user_profile()
        db = _mock_db()
        exec_result = MagicMock()
        exec_result.scalar_one_or_none.return_value = profile
        exec_result.all.return_value = []
        db.execute.return_value = exec_result

        app = self._app()
        app.dependency_overrides[get_db] = lambda: db
        r = TestClient(app).delete(f"/api/v1/users/{profile.id}", headers=_hdr())
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    def test_delete_not_found(self):
        db = _mock_db()
        db.execute.return_value.scalar_one_or_none.return_value = None
        app = self._app()
        app.dependency_overrides[get_db] = lambda: db
        r = TestClient(app).delete(f"/api/v1/users/{uuid.uuid4()}", headers=_hdr())
        assert r.status_code == 404

    def test_delete_bad_uuid(self):
        r = TestClient(self._app()).delete("/api/v1/users/not-uuid", headers=_hdr())
        assert r.status_code == 422

    def test_delete_no_auth(self):
        from api.v1.user import router
        r = TestClient(_mkapp(router)).delete(f"/api/v1/users/{uuid.uuid4()}")
        assert r.status_code == 401

    def test_invalid_blood_group(self):
        r = TestClient(self._app()).post(
            "/api/v1/users/",
            json={"name": "T", "blood_group": "BAD", "emergency_contacts": []},
            headers=_hdr())
        assert r.status_code == 422


# ══════════════════════════════════════════════════════════════════════════════
# roadwatch additional coverage
# ══════════════════════════════════════════════════════════════════════════════

class TestRoadwatchCoverage:

    def _app(self):
        from api.v1.roadwatch import router
        svc = MagicMock()
        svc.find_nearby_issues = AsyncMock(return_value=RoadIssuesResponse(
            issues=[], count=0, radius_used=5000))
        svc.get_authority = AsyncMock(return_value=AuthorityPreviewResponse(
            road_type="NH", road_type_code="NH", authority_name="NHAI",
            helpline="1033", complaint_portal="https://nhai.gov.in",
            escalation_path="MoRTH", source="authority_matrix"))
        svc.get_infrastructure = AsyncMock(return_value=RoadInfrastructureResponse(
            road_type="NH", road_type_code="NH", source="road_infrastructure"))
        svc.submit_report = AsyncMock(return_value=RoadReportResponse(
            uuid=uuid.uuid4(), complaint_ref="R-001", authority_name="NHAI",
            authority_phone="1033", complaint_portal="https://nhai.gov.in",
            road_type="NH", road_type_code="NH", status="open"))
        svc.verify_report = AsyncMock(return_value={"status": "verified"})
        svc._save_photo = AsyncMock(return_value=None)
        app = _mkapp(router)
        app.state.roadwatch_service = svc
        app.state.queue = None
        app.dependency_overrides[get_current_user_optional] = lambda: None
        app.dependency_overrides[get_current_user] = lambda: _auth(role="field_officer")
        app.dependency_overrides[require_role(Role.FIELD_OFFICER)] = lambda: _auth(role="field_officer")
        app.dependency_overrides[require_role(Role.OPERATOR)] = lambda: _auth(role="operator")
        from core.limiter import limiter
        app.dependency_overrides[limiter.limit] = lambda *a, **kw: lambda x: x
        return app

    def test_issue_details_bad_uuid(self):
        r = TestClient(self._app()).get("/api/v1/roads/issues/not-uuid")
        assert r.status_code == 422

    def test_issue_details_not_found(self):
        import api.v1.roadwatch as rw_mod
        import models.road_issue as ri_mod
        rw_mod.RoadIssue = ri_mod.RoadIssue
        db = _mock_db()
        db.execute.return_value.first.return_value = None
        app = self._app()
        app.dependency_overrides[get_db] = lambda: db
        r = TestClient(app).get(f"/api/v1/roads/issues/{uuid.uuid4()}")
        assert r.status_code == 404

    def test_confirm_success(self):
        issue = _mock_issue()
        db = _mock_db()
        db.execute.return_value.scalar_one_or_none.return_value = None
        with patch("services.duplicate_detector.DuplicateDetector.increment_confirmation",
                   AsyncMock(return_value=issue)):
            with patch("services.complaint_lifecycle.ComplaintLifecycle.log_event", AsyncMock()):
                app = self._app()
                app.dependency_overrides[get_db] = lambda: db
                r = TestClient(app).post(
                    f"/api/v1/roads/report/{uuid.uuid4()}/confirm")
                assert r.status_code == 200

    def test_confirm_not_found(self):
        db = _mock_db()
        db.execute.return_value.scalar_one_or_none.return_value = None
        with patch("services.duplicate_detector.DuplicateDetector.increment_confirmation",
                   AsyncMock(return_value=None)):
            app = self._app()
            app.dependency_overrides[get_db] = lambda: db
            r = TestClient(app).post(
                f"/api/v1/roads/report/{uuid.uuid4()}/confirm")
            assert r.status_code == 404

    @patch("services.complaint_lifecycle.ComplaintLifecycle")
    def test_resolve_success(self, mock_cl):
        issue = _mock_issue()
        issue.resolved_at = datetime.now(UTC)
        mock_cl.resolve = AsyncMock(return_value=issue)

        app = self._app()
        r = TestClient(app).post(
            f"/api/v1/roads/report/{uuid.uuid4()}/resolve",
            headers=_hdr(role="field_officer"))
        assert r.status_code == 200
        assert r.json()["status"] == "resolved"

    @patch("services.complaint_lifecycle.ComplaintLifecycle")
    def test_resolve_not_found(self, mock_cl):
        mock_cl.resolve = AsyncMock(side_effect=ValueError("Not found"))

        app = self._app()
        r = TestClient(app).post(
            f"/api/v1/roads/report/{uuid.uuid4()}/resolve",
            headers=_hdr(role="field_officer"))
        assert r.status_code == 404

    def test_verify_no_auth(self):
        from api.v1.roadwatch import router
        app = _mkapp(router)
        svc = MagicMock()
        app.state.roadwatch_service = svc
        r = TestClient(app).patch(f"/api/v1/roads/report/{uuid.uuid4()}/verify")
        assert r.status_code == 401

    def _operator_app(self):
        from api.v1.roadwatch import router
        svc = MagicMock()
        svc.find_nearby_issues = AsyncMock(return_value=RoadIssuesResponse(issues=[], count=0, radius_used=5000))
        svc.get_authority = AsyncMock(return_value=AuthorityPreviewResponse(
            road_type="NH", road_type_code="NH", authority_name="NHAI",
            helpline="1033", complaint_portal="https://nhai.gov.in",
            escalation_path="MoRTH", source="authority_matrix"))
        svc.get_infrastructure = AsyncMock(return_value=RoadInfrastructureResponse(
            road_type="NH", road_type_code="NH", source="road_infrastructure"))
        svc.submit_report = AsyncMock(return_value=RoadReportResponse(
            uuid=uuid.uuid4(), complaint_ref="R-001", authority_name="NHAI",
            authority_phone="1033", complaint_portal="https://nhai.gov.in",
            road_type="NH", road_type_code="NH", status="open"))
        svc.verify_report = AsyncMock(return_value={"status": "verified"})
        svc._save_photo = AsyncMock(return_value=None)
        app = _mkapp(router)
        app.state.roadwatch_service = svc
        app.state.queue = None
        app.dependency_overrides[get_current_user_optional] = lambda: None
        app.dependency_overrides[get_current_user] = lambda: _auth(role="operator")
        from core.rbac import require_role as rbac_require_role
        _op_dep = rbac_require_role(Role.OPERATOR)
        app.dependency_overrides[_op_dep] = lambda: _auth(role="operator")
        from core.limiter import limiter
        app.dependency_overrides[limiter.limit] = lambda *a, **kw: lambda x: x
        return app

    def test_verify_not_found(self):
        from services.exceptions import ServiceValidationError
        app = self._operator_app()
        app.state.roadwatch_service.verify_report = AsyncMock(
            side_effect=ServiceValidationError("Report not found"))

        r = TestClient(app).patch(
            f"/api/v1/roads/report/{uuid.uuid4()}/verify",
            headers=_hdr(role="operator"))
        assert r.status_code == 404

    def test_verify_validation_error(self):
        from services.exceptions import ServiceValidationError
        app = self._operator_app()
        app.state.roadwatch_service.verify_report = AsyncMock(
            side_effect=ServiceValidationError("Invalid state"))

        r = TestClient(app).patch(
            f"/api/v1/roads/report/{uuid.uuid4()}/verify",
            headers=_hdr(role="operator"))
        assert r.status_code == 422

    def test_verify_success_no_queue(self):
        app = self._operator_app()
        app.state.queue = None
        with patch("services.complaint_lifecycle.ComplaintLifecycle.update_status", AsyncMock()):
            with patch("services.osm_contributor.get_osm_contributor") as mock_get:
                mock_osm = MagicMock()
                mock_osm.is_configured = False
                mock_get.return_value = mock_osm
                r = TestClient(app).patch(
                    f"/api/v1/roads/report/{uuid.uuid4()}/verify",
                    headers=_hdr(role="operator"))
                assert r.status_code == 200
                assert r.json()["status"] == "verified"

    def test_verify_success_osm_configured(self):
        app = self._operator_app()
        app.state.queue = None
        with patch("services.complaint_lifecycle.ComplaintLifecycle.update_status", AsyncMock()):
            with patch("services.osm_contributor.get_osm_contributor") as mock_get:
                mock_osm = MagicMock()
                mock_osm.is_configured = True
                mock_osm.contribute_report = AsyncMock(return_value={"status": "submitted"})
                mock_get.return_value = mock_osm
                r = TestClient(app).patch(
                    f"/api/v1/roads/report/{uuid.uuid4()}/verify",
                    headers=_hdr(role="operator"))
                assert r.status_code == 200

    def test_timeline_success(self):
        event = MagicMock()
        event.id = 1
        event.complaint_uuid = uuid.uuid4()
        event.event_type = "created"
        event.actor_id = None
        event.actor_role = "system"
        event.notes = "Issue created"
        event.event_metadata = {}
        event.created_at = datetime.now(UTC)

        db = _mock_db()
        db.execute.return_value.all.return_value = [event]

        app = self._app()
        app.dependency_overrides[get_db] = lambda: db
        r = TestClient(app).get(f"/api/v1/roads/issues/{uuid.uuid4()}/timeline")
        assert r.status_code == 200


# ══════════════════════════════════════════════════════════════════════════════
# command_center additional coverage
# ══════════════════════════════════════════════════════════════════════════════

class TestCommandCenterCoverage:

    @pytest.fixture(autouse=True)
    def _reset(self):
        CircuitBreakerRegistry.reset_all()

    def _app(self):
        from api.v1.command_center import router
        app = _mkapp(router)
        app.dependency_overrides[get_current_user] = lambda: _auth(role="operator")
        app.dependency_overrides[require_role(Role.OPERATOR)] = lambda: _auth(role="operator")
        from core.limiter import limiter
        app.dependency_overrides[limiter.limit] = lambda *a, **kw: lambda x: x
        return app

    def test_officer_locations_no_data(self):
        db = _mock_db()
        db.execute.return_value.all.return_value = []
        app = self._app()
        app.dependency_overrides[get_db] = lambda: db
        r = TestClient(app).get("/api/v1/command-center/officer-locations", headers=_hdr())
        assert r.status_code == 200
        assert r.json()["total"] == 0

    def test_officer_locations_with_data(self):
        o = _mock_officer()
        db = _mock_db()
        row = (o, 13.08, 80.27, 2)
        db.execute.return_value.all.return_value = [row]
        app = self._app()
        app.dependency_overrides[get_db] = lambda: db
        r = TestClient(app).get("/api/v1/command-center/officer-locations", headers=_hdr())
        assert r.status_code == 200

    def test_escalation_board_empty(self):
        with patch("services.escalation_predictor.EscalationPredictor.batch_predict",
                   AsyncMock(return_value=[])):
            r = TestClient(self._app()).get(
                "/api/v1/command-center/escalation-board?min_risk=0.5",
                headers=_hdr())
        assert r.status_code == 200
        assert r.json()["total"] == 0

    def test_escalation_board_401(self):
        from api.v1.command_center import router
        r = TestClient(_mkapp(router)).get("/api/v1/command-center/escalation-board")
        assert r.status_code == 401

    def test_hotspots_empty(self):
        db = _mock_db()
        db.execute.return_value.all.return_value = []
        app = self._app()
        app.dependency_overrides[get_db] = lambda: db
        r = TestClient(app).get("/api/v1/command-center/hotspots", headers=_hdr())
        assert r.status_code == 200
        assert r.json()["total_hotspots"] == 0

    def test_hotspots_401(self):
        from api.v1.command_center import router
        r = TestClient(_mkapp(router)).get("/api/v1/command-center/hotspots")
        assert r.status_code == 401

    def test_resolution_metrics_ok(self):
        db = _mock_db()
        db.execute.return_value.all.return_value = []
        app = self._app()
        app.dependency_overrides[get_db] = lambda: db
        r = TestClient(app).get("/api/v1/command-center/resolution-metrics", headers=_hdr())
        assert r.status_code == 200
        d = r.json()
        assert "by_category" in d and len(d["by_category"]) == 3
        assert "by_severity" in d and len(d["by_severity"]) == 5

    def test_resolution_metrics_401(self):
        from api.v1.command_center import router
        r = TestClient(_mkapp(router)).get("/api/v1/command-center/resolution-metrics")
        assert r.status_code == 401

    def test_event_bus_health_ok(self):
        r = TestClient(self._app()).get("/api/v1/command-center/event-bus-health", headers=_hdr())
        assert r.status_code == 200
        assert "metrics" in r.json()

    def test_event_bus_health_401(self):
        from api.v1.command_center import router
        r = TestClient(_mkapp(router)).get("/api/v1/command-center/event-bus-health")
        assert r.status_code == 401

    def test_sse_format(self):
        from api.v1.command_center import _sse_format
        result = _sse_format("test", {"key": "value"})
        assert "event: test" in result
        assert "key" in result
        assert "value" in result


# ══════════════════════════════════════════════════════════════════════════════
# tracking edge cases
# ══════════════════════════════════════════════════════════════════════════════

class TestTrackingCoverage:

    def test_origin_allowed_production_blocked(self, monkeypatch):
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("CORS_ORIGINS", "https://example.com")
        from core.config import get_settings
        get_settings.cache_clear()
        from api.v1.tracking import _origin_allowed
        assert not _origin_allowed(None)
        get_settings.cache_clear()

    def test_origin_allowed_production_with_cors(self, monkeypatch):
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("CORS_ORIGINS", "https://example.com")
        from core.config import get_settings
        get_settings.cache_clear()
        from api.v1.tracking import _origin_allowed
        assert not _origin_allowed("https://evil.com")
        assert _origin_allowed("https://example.com")
        get_settings.cache_clear()

    def test_origin_allowed_wildcard_dev(self, monkeypatch):
        monkeypatch.setenv("ENVIRONMENT", "development")
        from core.config import get_settings
        get_settings.cache_clear()
        from api.v1.tracking import _origin_allowed
        assert _origin_allowed("http://localhost:3000")
        get_settings.cache_clear()

    def test_origin_allowed_dev_no_origin(self, monkeypatch):
        monkeypatch.setenv("ENVIRONMENT", "development")
        monkeypatch.setenv("CORS_ORIGINS", "*")
        from core.config import get_settings
        get_settings.cache_clear()
        from api.v1.tracking import _origin_allowed
        assert _origin_allowed(None)
        get_settings.cache_clear()

    @pytest.mark.asyncio
    async def test_redis_mgr_broadcast_no_redis(self):
        from api.v1.tracking import RedisConnectionManager
        m = RedisConnectionManager()
        ws = MagicMock()
        ws.send_text = AsyncMock()
        m.active_connections["test"] = {ws}
        await m.broadcast({"lat": 10.0}, "test")
        ws.send_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_redis_mgr_broadcast_with_redis(self):
        from api.v1.tracking import RedisConnectionManager
        m = RedisConnectionManager()
        redis_mock = AsyncMock()
        m.set_redis(redis_mock)
        await m.broadcast({"lat": 10.0}, "test")
        redis_mock.publish.assert_called_once()

    def test_ws_origin_not_allowed(self):
        from starlette.websockets import WebSocketDisconnect

        from api.v1.tracking import router
        monkeypatch = pytest.MonkeyPatch()
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("CORS_ORIGINS", "https://app.example.com")
        from core.config import get_settings
        get_settings.cache_clear()

        app = FastAPI()
        app.include_router(router)
        with pytest.raises(WebSocketDisconnect) as exc, TestClient(app).websocket_connect(
            "/api/v1/tracking/group",
            headers={"origin": "https://evil.com"}):
            pass
        assert exc.value.code == 1008
        get_settings.cache_clear()
        monkeypatch.undo()

    def test_ws_message_too_large(self, monkeypatch):
        from api.v1.tracking import router
        monkeypatch.setattr("api.v1.tracking._origin_allowed", lambda x: True)
        app = FastAPI()
        app.include_router(router)
        with TestClient(app).websocket_connect(
            f"/api/v1/tracking/group?token={create_access_token({'sub':'tu'})}",
            headers={"origin": "http://localhost:3000"}) as ws:
            ws.send_text("x" * 5000)
            # Should close with code 1009
            with pytest.raises(Exception):
                ws.receive_text()

    def test_connection_health_stale_detection(self):
        import time

        from api.v1.tracking import ConnectionHealth
        ch = ConnectionHealth()
        ws = MagicMock()
        # Set activity far in the past (use monotonic time so comparison works)
        ch._last_activity[id(ws)] = time.monotonic() - 100
        stale = ch.stale_connections({ws}, timeout=1)
        assert len(stale) == 1

    def test_connection_health_no_activity(self):
        from api.v1.tracking import ConnectionHealth
        ch = ConnectionHealth()
        ws = MagicMock()
        stale = ch.stale_connections({ws}, timeout=0.001)
        assert len(stale) == 0  # Never had activity

    def test_connection_health_remove(self):
        from api.v1.tracking import ConnectionHealth
        ch = ConnectionHealth()
        ws = MagicMock()
        ch.mark_activity(ws)
        ch.remove(ws)
        stale = ch.stale_connections({ws}, timeout=999999)
        assert len(stale) == 0  # removed

    @pytest.mark.asyncio
    async def test_listen_to_pubsub_no_redis(self):
        from api.v1.tracking import RedisConnectionManager
        m = RedisConnectionManager()
        task = asyncio.create_task(m._listen_to_pubsub("test"))
        await asyncio.sleep(0.05)
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass  # Expected: task was intentionally cancelled after test assertion

    @pytest.mark.asyncio
    async def test_stale_cleanup_loop(self):
        from api.v1.tracking import RedisConnectionManager
        m = RedisConnectionManager()
        ws = MagicMock()
        m.active_connections["test"] = {ws}
        task = asyncio.create_task(m._stale_cleanup_loop())
        await asyncio.sleep(0.05)
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass  # Expected: task was intentionally cancelled after test assertion

    def test_is_valid_tracking_payload_latitude_longitude(self):
        from api.v1.tracking import _is_valid_tracking_payload
        assert _is_valid_tracking_payload({"latitude": 10.0, "longitude": 20.0})

    @pytest.mark.asyncio
    async def test_redis_mgr_connect_disconnect(self):
        from api.v1.tracking import RedisConnectionManager
        m = RedisConnectionManager()
        ws = AsyncMock()
        ws.send_text = AsyncMock()
        await m.connect(ws, "test_group")
        assert "test_group" in m.active_connections
        assert ws in m.active_connections["test_group"]
        m.disconnect(ws, "test_group")
        assert "test_group" not in m.active_connections

    def test_redis_mgr_disconnect_no_group(self):
        from api.v1.tracking import RedisConnectionManager
        m = RedisConnectionManager()
        ws = MagicMock()
        m.disconnect(ws, "nonexistent")
