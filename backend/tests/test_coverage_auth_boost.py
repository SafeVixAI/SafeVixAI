# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Coverage boost for auth and admin API routes."""
from __future__ import annotations

import hashlib
import os
import uuid as _uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

os.environ.setdefault("APP_ENV", "test")
import core.limiter

core.limiter.limiter.enabled = False

import jwt
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from core.database import get_db
from core.security import (
    ALGORITHM,
    APP_JWT_AUDIENCE,
    APP_JWT_ISSUER,
    SECRET_KEY,
    create_access_token,
    create_refresh_token,
)


def _make_token(sub="test@example.com", role="operator", name="Test Operator"):
    return create_access_token(data={"sub": sub, "name": name}, role=role)


def _hash_for_test(password: str, salt: str = "aabbccdd11223344556677889900ff01") -> str:
    iterations = 1000
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), iterations).hex()
    return f"pbkdf2_sha256${iterations}${salt}${digest}"


# ═══════════════════════════════════════════════════════════════════════════════
# AUTH API TESTS
# ═══════════════════════════════════════════════════════════════════════════════


class TestAuthCsrfToken:
    """GET /api/v1/auth/csrf-token"""

    @pytest.fixture
    def client(self):
        from api.v1 import auth
        app = FastAPI()
        app.include_router(auth.router)
        return TestClient(app)

    def test_get_csrf_token(self, client):
        resp = client.get("/api/v1/auth/csrf-token")
        assert resp.status_code == 200
        data = resp.json()
        assert "csrf_token" in data
        assert len(data["csrf_token"]) > 0
        assert "csrf_token" in resp.cookies


class TestAuthRegister:
    """POST /api/v1/auth/register"""

    @pytest.fixture
    def mock_db(self):
        return AsyncMock()

    @pytest.fixture
    def client(self, mock_db):
        from api.v1 import auth
        app = FastAPI()
        async def override_db():
            yield mock_db
        app.dependency_overrides[get_db] = override_db
        app.include_router(auth.router)
        return TestClient(app)

    def test_duplicate_email(self, client, mock_db):
        existing = MagicMock()
        existing.email = "dup@example.com"
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = existing
        mock_db.execute.return_value = result_mock
        resp = client.post("/api/v1/auth/register", json={
            "email": "dup@example.com",
            "password": "testpass123",
            "name": "Duplicate",
        })
        assert resp.status_code == 400
        assert "already exists" in resp.json()["detail"].lower()

    @patch("api.v1.auth.AuditLog.log_auth_login")
    def test_register_success(self, mock_audit, client, mock_db):
        not_found = MagicMock()
        not_found.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = not_found
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        resp = client.post("/api/v1/auth/register", json={
            "email": "new@example.com",
            "password": "testpass123",
            "name": "New User",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["message"] == "Operator registered successfully"
        assert data["operator_name"] == "New User"
        assert data["email"] == "new@example.com"


class TestAuthLogin:
    """POST /api/v1/auth/login"""

    @pytest.fixture
    def mock_db(self):
        return AsyncMock()

    @pytest.fixture
    def client(self, mock_db):
        from api.v1 import auth
        app = FastAPI()
        async def override_db():
            yield mock_db
        app.dependency_overrides[get_db] = override_db
        app.include_router(auth.router)
        return TestClient(app)

    def test_invalid_credentials(self, client, mock_db):
        not_found = MagicMock()
        not_found.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = not_found
        resp = client.post("/api/v1/auth/login", json={
            "email": "unknown@example.com",
            "password": "wrongpass123",
        })
        assert resp.status_code == 401
        assert "invalid" in resp.json()["detail"].lower()

    def test_db_operator_success(self, client, mock_db):
        password = "testpass123"
        user = MagicMock()
        user.email = "operator@example.com"
        user.name = "DB Operator"
        user.role = "operator"
        user.hashed_password = _hash_for_test(password)
        user.is_active = True
        found = MagicMock()
        found.scalar_one_or_none.return_value = user
        mock_db.execute.return_value = found
        resp = client.post("/api/v1/auth/login", json={
            "email": "operator@example.com",
            "password": password,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["message"] == "Login successful"
        assert data["operator_name"] == "DB Operator"
        assert "access_token" in resp.cookies

    def test_env_operator_fallback(self, client, mock_db, monkeypatch):
        not_found = MagicMock()
        not_found.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = not_found
        password = "envpass789"
        pw_hash = _hash_for_test(password)
        monkeypatch.setenv("AUTH_OPERATOR_EMAIL", "env-admin@example.com")
        monkeypatch.setenv("AUTH_OPERATOR_PASSWORD_HASH", pw_hash)
        monkeypatch.setenv("AUTH_OPERATOR_NAME", "Env Admin")
        resp = client.post("/api/v1/auth/login", json={
            "email": "env-admin@example.com",
            "password": password,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["message"] == "Login successful"
        assert data["operator_name"] == "Env Admin"
        assert "access_token" in resp.cookies

    def test_wrong_env_password(self, client, mock_db, monkeypatch):
        not_found = MagicMock()
        not_found.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = not_found
        pw_hash = _hash_for_test("correctpass")
        monkeypatch.setenv("AUTH_OPERATOR_EMAIL", "env-admin@example.com")
        monkeypatch.setenv("AUTH_OPERATOR_PASSWORD_HASH", pw_hash)
        monkeypatch.setenv("AUTH_OPERATOR_NAME", "Env Admin")
        resp = client.post("/api/v1/auth/login", json={
            "email": "env-admin@example.com",
            "password": "wrongpass",
        })
        assert resp.status_code == 401


class TestAuthRefresh:
    """POST /api/v1/auth/refresh"""

    @pytest.fixture
    def client(self):
        from api.v1 import auth
        app = FastAPI()
        app.include_router(auth.router)
        return TestClient(app)

    def test_expired_token(self, client):
        expired = jwt.encode(
            {
                "sub": "test@example.com",
                "exp": datetime.now(UTC) - timedelta(hours=1),
                "aud": APP_JWT_AUDIENCE,
                "iss": APP_JWT_ISSUER,
                "purpose": "refresh",
                "jti": "expired-jti",
            },
            SECRET_KEY,
            algorithm=ALGORITHM,
        )
        resp = client.post("/api/v1/auth/refresh", json={"refresh_token": expired})
        assert resp.status_code == 401
        assert "expired" in resp.json()["detail"].lower()

    def test_invalid_purpose(self, client):
        access = _make_token()
        resp = client.post("/api/v1/auth/refresh", json={"refresh_token": access})
        assert resp.status_code == 401
        assert "purpose" in resp.json()["detail"].lower()

    def test_invalid_token(self, client):
        resp = client.post("/api/v1/auth/refresh", json={"refresh_token": "x" * 30})
        assert resp.status_code == 401

    def test_refresh_success(self, client):
        refresh = create_refresh_token({
            "sub": "ref@example.com",
            "name": "Ref User",
            "role": "operator",
        })
        resp = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh})
        assert resp.status_code == 200
        data = resp.json()
        assert data["message"] == "Token refreshed successfully"
        assert "access_token" in resp.cookies


class TestAuthRevoke:
    """POST /api/v1/auth/revoke"""

    @pytest.fixture
    def client(self):
        from api.v1 import auth
        app = FastAPI()
        app.include_router(auth.router)
        return TestClient(app)

    def test_revoke_success(self, client):
        token = _make_token()
        resp = client.post("/api/v1/auth/revoke", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert resp.json()["message"] == "Token revoked successfully"

    def test_revoke_no_auth(self, client):
        resp = client.post("/api/v1/auth/revoke")
        assert resp.status_code == 401


class TestAuthVerify:
    """GET /api/v1/auth/verify"""

    @pytest.fixture
    def client(self):
        from api.v1 import auth
        app = FastAPI()
        app.include_router(auth.router)
        return TestClient(app)

    def test_valid_token(self, client):
        token = _make_token(sub="verify@example.com", role="operator")
        resp = client.get("/api/v1/auth/verify", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "valid"
        assert data["sub"] == "verify@example.com"
        assert data["role"] == "operator"

    def test_no_token(self, client):
        resp = client.get("/api/v1/auth/verify")
        assert resp.status_code == 401


class TestAuthLogout:
    """POST /api/v1/auth/logout"""

    @pytest.fixture
    def client(self):
        from api.v1 import auth
        app = FastAPI()
        app.include_router(auth.router)
        return TestClient(app)

    def test_logout_success(self, client):
        resp = client.post("/api/v1/auth/logout")
        assert resp.status_code == 200
        assert resp.json()["message"] == "Logged out successfully"
        set_cookie = resp.headers.get("set-cookie", "")
        assert "access_token=" in set_cookie
        assert "Max-Age=0" in set_cookie or "expires=" in set_cookie


# ═══════════════════════════════════════════════════════════════════════════════
# ADMIN API TESTS
# ═══════════════════════════════════════════════════════════════════════════════


def _make_issue_mock(idx=1):
    issue = MagicMock()
    issue.uuid = _uuid.UUID("550e8400-e29b-41d4-a716-446655440000")
    issue.complaint_ref = f"REF-{idx:04d}"
    issue.issue_type = "pothole"
    issue.severity = 3
    issue.description = f"Test issue {idx}"
    issue.location_address = "Test Location"
    issue.road_name = "Main Road"
    issue.road_type = "highway"
    issue.road_number = "NH-48"
    issue.authority_name = "PWD"
    issue.status = "open"
    issue.created_at = datetime.now(UTC)
    issue.category = "roads"
    issue.sub_category = "pothole"
    issue.ward_id = "ward-01"
    issue.ward_name = "Ward 1"
    issue.assigned_officer_id = None
    issue.sla_deadline = None
    issue.resolved_at = None
    issue.duplicate_of_uuid = None
    issue.confirmation_count = 0
    issue.before_photo_url = None
    issue.after_photo_url = None
    return issue


class TestAdminComplaints:
    """GET /api/v1/admin/complaints"""

    @pytest.fixture
    def mock_db(self):
        return AsyncMock()

    @pytest.fixture
    def client(self, mock_db):
        from api.v1 import admin
        app = FastAPI()
        async def override_db():
            yield mock_db
        app.dependency_overrides[get_db] = override_db
        app.include_router(admin.router)
        return TestClient(app)

    @pytest.fixture
    def auth_header(self):
        token = _make_token(role="operator")
        return {"Authorization": f"Bearer {token}"}

    def test_list_complaints_success(self, client, mock_db, auth_header):
        rows = [(_make_issue_mock(i), 13.0 + i, 80.0 + i) for i in range(3)]
        count_result = MagicMock()
        count_result.scalar.return_value = 3
        data_result = MagicMock()
        data_result.all.return_value = rows
        mock_db.execute.side_effect = [count_result, data_result]
        resp = client.get("/api/v1/admin/complaints", headers=auth_header)
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 3
        assert len(data["issues"]) == 3
        assert data["total_count"] == 3

    def test_list_complaints_with_filters(self, client, mock_db, auth_header):
        rows = [(_make_issue_mock(1), 13.0, 80.0)]
        count_result = MagicMock()
        count_result.scalar.return_value = 1
        data_result = MagicMock()
        data_result.all.return_value = rows
        mock_db.execute.side_effect = [count_result, data_result]
        resp = client.get(
            "/api/v1/admin/complaints?status=open&category=roads&ward_id=ward-01",
            headers=auth_header,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 1

    def test_list_complaints_no_auth(self, client):
        resp = client.get("/api/v1/admin/complaints")
        assert resp.status_code == 403 or resp.status_code == 401

    def test_list_complaints_insufficient_role(self, client, auth_header):
        low_token = _make_token(role="user")
        resp = client.get(
            "/api/v1/admin/complaints",
            headers={"Authorization": f"Bearer {low_token}"},
        )
        assert resp.status_code == 403


class TestAdminAssignComplaint:
    """POST /api/v1/admin/complaints/{uuid}/assign"""

    @pytest.fixture
    def mock_db(self):
        return AsyncMock()

    @pytest.fixture
    def client(self, mock_db):
        from api.v1 import admin
        app = FastAPI()
        async def override_db():
            yield mock_db
        app.dependency_overrides[get_db] = override_db
        app.include_router(admin.router)
        return TestClient(app)

    @pytest.fixture
    def auth_header(self):
        token = _make_token(sub="550e8400-e29b-41d4-a716-446655440000", role="operator")
        return {"Authorization": f"Bearer {token}"}

    VALID_UUID = "550e8400-e29b-41d4-a716-446655440000"

    def test_invalid_uuid_format(self, client, auth_header):
        resp = client.post(
            f"/api/v1/admin/complaints/not-a-uuid/assign?officer_id={self.VALID_UUID}",
            headers=auth_header,
        )
        assert resp.status_code == 422

    @patch("api.v1.admin.ComplaintLifecycle", autospec=False)
    def test_assign_success(self, mock_lifecycle, client, mock_db, auth_header):
        mock_issue = MagicMock()
        mock_issue.complaint_ref = "REF-001"
        mock_issue.assigned_officer_id = self.VALID_UUID
        mock_issue.sla_deadline = datetime.now(UTC)
        mock_lifecycle.assign_officer = AsyncMock(return_value=mock_issue)
        resp = client.post(
            f"/api/v1/admin/complaints/{self.VALID_UUID}/assign?officer_id={self.VALID_UUID}",
            headers=auth_header,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "assigned"
        assert data["complaint_ref"] == "REF-001"

    @patch("api.v1.admin.ComplaintLifecycle", autospec=False)
    def test_assign_not_found(self, mock_lifecycle, client, mock_db, auth_header):
        mock_lifecycle.assign_officer = MagicMock(
            side_effect=ValueError("Officer not found")
        )
        resp = client.post(
            f"/api/v1/admin/complaints/{self.VALID_UUID}/assign?officer_id={self.VALID_UUID}",
            headers=auth_header,
        )
        assert resp.status_code == 404

    def test_assign_no_auth(self, client):
        resp = client.post(
            f"/api/v1/admin/complaints/{self.VALID_UUID}/assign?officer_id={self.VALID_UUID}",
        )
        assert resp.status_code == 401


class TestAdminOfficers:
    """GET /api/v1/admin/officers"""

    @pytest.fixture
    def mock_db(self):
        return AsyncMock()

    @pytest.fixture
    def client(self, mock_db):
        from api.v1 import admin
        app = FastAPI()
        async def override_db():
            yield mock_db
        app.dependency_overrides[get_db] = override_db
        app.include_router(admin.router)
        return TestClient(app)

    @pytest.fixture
    def auth_header(self):
        token = _make_token(role="operator")
        return {"Authorization": f"Bearer {token}"}

    def test_list_officers_success(self, client, mock_db, auth_header):
        officer = MagicMock()
        officer.id = _uuid.UUID("550e8400-e29b-41d4-a716-446655440000")
        officer.name = "Field Officer"
        officer.phone = "9999999999"
        officer.email = "fo@example.com"
        officer.role = "field_officer"
        officer.ward_id = "ward-01"
        officer.department = "PWD"
        officer.is_active = True
        officer.last_checkin = datetime.now(UTC)
        officer.created_at = datetime.now(UTC)
        scalars_mock = MagicMock()
        scalars_mock.all.return_value = [officer]
        result_mock = MagicMock()
        result_mock.scalars.return_value = scalars_mock
        mock_db.execute.return_value = result_mock
        resp = client.get("/api/v1/admin/officers", headers=auth_header)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["name"] == "Field Officer"

    def test_list_officers_no_auth(self, client):
        resp = client.get("/api/v1/admin/officers")
        assert resp.status_code in (401, 403)


class TestAdminDashboard:
    """GET /api/v1/admin/dashboard"""

    @pytest.fixture
    def mock_db(self):
        return AsyncMock()

    @pytest.fixture
    def client(self, mock_db):
        from api.v1 import admin
        app = FastAPI()
        async def override_db():
            yield mock_db
        app.dependency_overrides[get_db] = override_db
        app.include_router(admin.router)
        return TestClient(app)

    @pytest.fixture
    def auth_header(self):
        token = _make_token(role="operator")
        return {"Authorization": f"Bearer {token}"}

    def test_dashboard_success(self, client, mock_db, auth_header):
        mock_result = MagicMock()
        mock_result.scalar.return_value = 5
        mock_result.all.return_value = [("roads", 3), ("traffic", 2)]
        mock_db.execute.return_value = mock_result
        resp = client.get("/api/v1/admin/dashboard", headers=auth_header)
        assert resp.status_code == 200
        data = resp.json()
        kpis = data["kpis"]
        assert kpis["total_complaints"] == 5
        assert kpis["active_complaints"] == 5
        assert kpis["resolved_complaints"] == 5
        assert kpis["active_field_officers"] == 5
        assert data["category_breakdown"]["roads"] == 3
        assert data["category_breakdown"]["traffic"] == 2


class TestAdminCleanup:
    """POST /api/v1/admin/cleanup-expired-data"""

    @pytest.fixture
    def mock_db(self):
        return AsyncMock()

    @pytest.fixture
    def client(self, mock_db):
        from api.v1 import admin
        app = FastAPI()
        async def override_db():
            yield mock_db
        app.dependency_overrides[get_db] = override_db
        app.include_router(admin.router)
        return TestClient(app)

    @pytest.fixture
    def auth_header(self):
        token = _make_token(role="operator")
        return {"Authorization": f"Bearer {token}"}

    def test_cleanup_success(self, client, mock_db, auth_header):
        mock_db.execute = AsyncMock()
        mock_db.commit = AsyncMock()
        resp = client.post("/api/v1/admin/cleanup-expired-data", headers=auth_header)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert "cleanup" in data["message"].lower()
