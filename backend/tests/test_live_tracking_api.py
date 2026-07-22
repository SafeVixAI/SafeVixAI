# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Live Tracking API tests for SafeVixAI backend."""
from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from api.v1 import live_tracking

# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_current_user():
    """Mock authenticated user."""
    return {"sub": "test-user-id", "role": "user"}


@pytest.fixture
def mock_db_session():
    """Mock database session."""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    return session


@pytest.fixture
def test_client(mock_current_user):
    """Create test client with auth override."""
    from fastapi import FastAPI

    app = FastAPI()

    async def mock_auth():
        return mock_current_user

    app.include_router(live_tracking.router)
    app.dependency_overrides[live_tracking.get_current_user] = mock_auth

    return TestClient(app)


# ── Start Tracking Tests ────────────────────────────────────────────────────

class TestStartTracking:
    """Tests for POST /start endpoint."""

    def test_start_tracking_success(self, test_client, mock_db_session):
        """Test successful tracking session creation."""
        with patch("api.v1.live_tracking.get_async_session") as mock_get_session:
            async def mock_gen():
                yield mock_db_session

            mock_get_session.side_effect = mock_gen

            response = test_client.post(
                "/api/v1/live-tracking/start",
                json={
                    "user_name": "Test User",
                    "latitude": 13.0827,
                    "longitude": 80.2707,
                    "blood_group": "O+",
                    "vehicle_number": "TN01AB1234",
                    "battery_percent": 85,
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert "session_id" in data
            assert "tracking_url" in data
            assert "expires_at" in data
            assert "/track/" in data["tracking_url"]

    def test_start_tracking_minimal_payload(self, test_client, mock_db_session):
        """Test tracking with minimal required fields."""
        with patch("api.v1.live_tracking.get_async_session") as mock_get_session:
            async def mock_gen():
                yield mock_db_session

            mock_get_session.side_effect = mock_gen

            response = test_client.post(
                "/api/v1/live-tracking/start",
                json={
                    "user_name": "Test User",
                    "latitude": 13.0827,
                    "longitude": 80.2707,
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert "session_id" in data

    def test_start_tracking_invalid_coordinates(self, test_client):
        """Test rejection of invalid coordinates."""
        response = test_client.post(
            "/api/v1/live-tracking/start",
            json={
                "user_name": "Test User",
                "latitude": 100.0,
                "longitude": 80.2707,
            }
        )
        assert response.status_code == 422

    def test_start_tracking_invalid_blood_group(self, test_client, mock_db_session):
        """Test rejection of invalid blood group format."""
        with patch("api.v1.live_tracking.get_async_session") as mock_get_session:
            async def mock_gen():
                yield mock_db_session

            mock_get_session.side_effect = mock_gen

            response = test_client.post(
                "/api/v1/live-tracking/start",
                json={
                    "user_name": "Test User",
                    "latitude": 13.0827,
                    "longitude": 80.2707,
                    "blood_group": "Invalid",
                }
            )
            assert response.status_code == 422

    def test_start_tracking_invalid_battery(self, test_client, mock_db_session):
        """Test rejection of invalid battery percentage."""
        with patch("api.v1.live_tracking.get_async_session") as mock_get_session:
            async def mock_gen():
                yield mock_db_session

            mock_get_session.side_effect = mock_gen

            response = test_client.post(
                "/api/v1/live-tracking/start",
                json={
                    "user_name": "Test User",
                    "latitude": 13.0827,
                    "longitude": 80.2707,
                    "battery_percent": 150,
                }
            )
            assert response.status_code == 422


# ── Update Location Tests ───────────────────────────────────────────────────

class TestUpdateLocation:
    """Tests for PUT /update endpoint."""

    def test_update_location_success(self, test_client, mock_db_session):
        """Test successful location update."""
        session_id = str(uuid.uuid4())

        mock_result = MagicMock()
        mock_result.fetchone = MagicMock(return_value=MagicMock(session_id=session_id))
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        with patch("api.v1.live_tracking.get_async_session") as mock_get_session:
            async def mock_gen():
                yield mock_db_session

            mock_get_session.side_effect = mock_gen

            response = test_client.put(
                "/api/v1/live-tracking/update",
                json={
                    "session_id": session_id,
                    "latitude": 13.0850,
                    "longitude": 80.2730,
                    "accuracy": 15.5,
                    "speed_kmh": 45.0,
                    "battery_percent": 75,
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "updated"

    def test_update_location_session_not_found(self, test_client, mock_db_session):
        """Test update when session doesn't exist."""
        session_id = str(uuid.uuid4())

        mock_result = MagicMock()
        mock_result.fetchone = MagicMock(return_value=None)
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        with patch("api.v1.live_tracking.get_async_session") as mock_get_session:
            async def mock_gen():
                yield mock_db_session

            mock_get_session.side_effect = mock_gen

            response = test_client.put(
                "/api/v1/live-tracking/update",
                json={
                    "session_id": session_id,
                    "latitude": 13.0850,
                    "longitude": 80.2730,
                }
            )

            assert response.status_code == 404
            assert "not found" in response.json()["detail"].lower()

    def test_update_location_invalid_coordinates(self, test_client):
        """Test rejection of invalid coordinates."""
        response = test_client.put(
            "/api/v1/live-tracking/update",
            json={
                "session_id": str(uuid.uuid4()),
                "latitude": 200.0,
                "longitude": 80.2730,
            }
        )
        assert response.status_code == 422

    def test_update_location_invalid_speed(self, test_client):
        """Test rejection of unrealistic speed."""
        response = test_client.put(
            "/api/v1/live-tracking/update",
            json={
                "session_id": str(uuid.uuid4()),
                "latitude": 13.0850,
                "longitude": 80.2730,
                "speed_kmh": 500.0,
            }
        )
        assert response.status_code == 422


# ── Get Session Tests ───────────────────────────────────────────────────────

class TestGetSession:
    """Tests for GET /session/{session_id} endpoint."""

    def test_get_session_with_token(self, test_client, mock_db_session):
        """Test successful session retrieval with valid token."""
        session_id = uuid.uuid4()

        from datetime import timedelta

        import jwt

        from core.security import ALGORITHM, SECRET_KEY

        view_token = jwt.encode(
            {
                "sub": str(session_id),
                "purpose": "tracking_view",
                "exp": datetime.now(UTC) + timedelta(hours=4),
            },
            SECRET_KEY,
            algorithm=ALGORITHM,
        )

        mock_row = MagicMock()
        mock_row.session_id = session_id
        mock_row.user_name = "Test User"
        mock_row.blood_group = "O+"
        mock_row.vehicle_number = "TN01AB1234"
        mock_row.latitude = 13.0827
        mock_row.longitude = 80.2707
        mock_row.accuracy = 10.5
        mock_row.speed_kmh = 30.0
        mock_row.battery_percent = 80
        mock_row.is_active = True
        mock_row.updated_at = datetime.now(UTC)

        mock_result = MagicMock()
        mock_result.fetchone = MagicMock(return_value=mock_row)
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        with patch("api.v1.live_tracking.get_async_session") as mock_get_session:
            async def mock_gen():
                yield mock_db_session

            mock_get_session.side_effect = mock_gen

            response = test_client.get(
                f"/api/v1/live-tracking/session/{session_id}",
                params={"token": view_token}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["user_name"] == "Test User"
            assert data["blood_group"] == "O+"
            assert data["is_active"] is True

    def test_get_session_with_bearer_token(self, test_client, mock_db_session):
        """Test session retrieval with Bearer token in header."""
        session_id = uuid.uuid4()

        from datetime import timedelta

        import jwt

        from core.security import ALGORITHM, SECRET_KEY

        # Create token directly with the module's SECRET_KEY
        view_token = jwt.encode(
            {
                "sub": str(session_id),
                "purpose": "tracking_view",
                "exp": datetime.now(UTC) + timedelta(hours=4),
            },
            SECRET_KEY,
            algorithm=ALGORITHM,
        )

        mock_row = MagicMock()
        mock_row.session_id = session_id
        mock_row.user_name = "Test User"
        mock_row.blood_group = None
        mock_row.vehicle_number = None
        mock_row.latitude = 13.0827
        mock_row.longitude = 80.2707
        mock_row.accuracy = None
        mock_row.speed_kmh = None
        mock_row.battery_percent = None
        mock_row.is_active = True
        mock_row.updated_at = datetime.now(UTC)

        mock_result = MagicMock()
        mock_result.fetchone = MagicMock(return_value=mock_row)
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        with patch("api.v1.live_tracking.get_async_session") as mock_get_session:
            async def mock_gen():
                yield mock_db_session

            mock_get_session.side_effect = mock_gen

            response = test_client.get(
                f"/api/v1/live-tracking/session/{session_id}",
                headers={"Authorization": f"Bearer {view_token}"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["user_name"] == "Test User"

    def test_get_session_missing_token(self, test_client):
        """Test rejection when no token provided."""
        session_id = uuid.uuid4()

        response = test_client.get(f"/api/v1/live-tracking/session/{session_id}")
        assert response.status_code == 403
        assert "token required" in response.json()["detail"].lower()

    def test_get_session_invalid_token(self, test_client):
        """Test rejection with invalid token format."""
        session_id = uuid.uuid4()

        response = test_client.get(
            f"/api/v1/live-tracking/session/{session_id}",
            params={"token": "invalid-token-that-is-long-enough-to-pass-validation"}
        )
        assert response.status_code == 403

    def test_get_session_wrong_purpose(self, test_client):
        """Test rejection with token for wrong purpose."""
        session_id = uuid.uuid4()

        from datetime import timedelta

        import jwt

        from core.security import ALGORITHM, SECRET_KEY

        wrong_token = jwt.encode(
            {
                "sub": "other-session",
                "purpose": "other_purpose",
                "exp": datetime.now(UTC) + timedelta(hours=4),
            },
            SECRET_KEY,
            algorithm=ALGORITHM,
        )

        response = test_client.get(
            f"/api/v1/live-tracking/session/{session_id}",
            params={"token": wrong_token}
        )
        assert response.status_code == 403

    def test_get_session_expired_token(self, test_client):
        """Test rejection with expired token."""
        session_id = uuid.uuid4()

        from datetime import timedelta

        import jwt

        from core.security import ALGORITHM, SECRET_KEY

        expired_token = jwt.encode(
            {
                "sub": str(session_id),
                "purpose": "tracking_view",
                "exp": datetime.now(UTC) - timedelta(hours=1),
            },
            SECRET_KEY,
            algorithm=ALGORITHM,
        )

        response = test_client.get(
            f"/api/v1/live-tracking/session/{session_id}",
            params={"token": expired_token}
        )
        assert response.status_code == 403

    def test_get_session_not_found(self, test_client, mock_db_session):
        """Test session not found in database."""
        session_id = uuid.uuid4()

        from datetime import timedelta

        import jwt

        from core.security import ALGORITHM, SECRET_KEY

        view_token = jwt.encode(
            {
                "sub": str(session_id),
                "purpose": "tracking_view",
                "exp": datetime.now(UTC) + timedelta(hours=4),
            },
            SECRET_KEY,
            algorithm=ALGORITHM,
        )

        mock_result = MagicMock()
        mock_result.fetchone = MagicMock(return_value=None)
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        with patch("api.v1.live_tracking.get_async_session") as mock_get_session:
            async def mock_gen():
                yield mock_db_session

            mock_get_session.side_effect = mock_gen

            response = test_client.get(
                f"/api/v1/live-tracking/session/{session_id}",
                params={"token": view_token}
            )

            assert response.status_code == 404


# ── Stop Tracking Tests ─────────────────────────────────────────────────────

class TestStopTracking:
    """Tests for DELETE /session/{session_id} endpoint."""

    def test_stop_tracking_success(self, test_client, mock_db_session):
        """Test successful session deactivation."""
        session_id = uuid.uuid4()

        mock_result = MagicMock()
        mock_result.fetchone = MagicMock(return_value=MagicMock(session_id=session_id))
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        with patch("api.v1.live_tracking.get_async_session") as mock_get_session:
            async def mock_gen():
                yield mock_db_session

            mock_get_session.side_effect = mock_gen

            response = test_client.delete(f"/api/v1/live-tracking/session/{session_id}")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "stopped"

    def test_stop_tracking_not_found(self, test_client, mock_db_session):
        """Test stopping non-existent session."""
        session_id = uuid.uuid4()

        mock_result = MagicMock()
        mock_result.fetchone = MagicMock(return_value=None)
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        with patch("api.v1.live_tracking.get_async_session") as mock_get_session:
            async def mock_gen():
                yield mock_db_session

            mock_get_session.side_effect = mock_gen

            response = test_client.delete(f"/api/v1/live-tracking/session/{session_id}")

            assert response.status_code == 404
            assert "not found" in response.json()["detail"].lower()


# ── Schema Validation Tests ─────────────────────────────────────────────────

class TestSchemaValidation:
    """Tests for request/response schema validation."""

    def test_start_tracking_request_valid(self):
        """Test valid start tracking request schema."""
        from api.v1.live_tracking import StartTrackingRequest

        request = StartTrackingRequest(
            user_name="Test User",
            latitude=13.0827,
            longitude=80.2707,
            blood_group="O+",
            vehicle_number="TN01AB1234",
            battery_percent=85,
        )

        assert request.user_name == "Test User"
        assert request.latitude == 13.0827
        assert request.blood_group == "O+"

    def test_update_location_request_valid(self):
        """Test valid update location request schema."""
        from api.v1.live_tracking import UpdateLocationRequest

        request = UpdateLocationRequest(
            session_id=uuid.uuid4(),
            latitude=13.0850,
            longitude=80.2730,
            accuracy=15.5,
            speed_kmh=45.0,
            battery_percent=75,
        )

        assert request.latitude == 13.0850
        assert request.speed_kmh == 45.0

    def test_tracking_session_response_schema(self):
        """Test tracking session response schema."""
        from api.v1.live_tracking import TrackingSessionResponse

        response = TrackingSessionResponse(
            session_id=str(uuid.uuid4()),
            user_name="Test User",
            blood_group="O+",
            vehicle_number="TN01AB1234",
            latitude=13.0827,
            longitude=80.2707,
            accuracy=10.5,
            speed_kmh=30.0,
            battery_percent=80,
            is_active=True,
            updated_at=datetime.now(UTC).isoformat(),
        )

        assert response.is_active is True
        assert response.user_name == "Test User"
