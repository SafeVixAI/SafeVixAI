# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Emergency API tests for SafeVixAI backend."""
from __future__ import annotations

from datetime import UTC
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from api.v1 import emergency

# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_emergency_service():
    """Mock emergency locator service."""
    service = MagicMock()
    service.find_nearby = AsyncMock()
    service.build_sos_payload = AsyncMock()
    return service


@pytest.fixture
def mock_db_session():
    """Mock database session."""
    session = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    return session


@pytest.fixture
def test_client(mock_emergency_service, mock_db_session):
    """Create test client with service overrides."""
    from fastapi import FastAPI

    from core.database import get_db

    app = FastAPI()

    # Mock app state
    app.state.emergency_service = mock_emergency_service

    async def override_db():
        yield mock_db_session

    app.dependency_overrides[get_db] = override_db

    app.include_router(emergency.router)

    return TestClient(app)


# ── Get Nearby Services Tests ───────────────────────────────────────────────

class TestGetNearbyServices:
    """Tests for GET /nearby endpoint."""

    def test_get_nearby_services_success(self, test_client, mock_emergency_service):
        """Test successful nearby services lookup."""
        from models.schemas import EmergencyResponse, EmergencyServiceItem

        mock_result = EmergencyResponse(
            services=[
                EmergencyServiceItem(
                    id="1",
                    name="City Hospital",
                    category="hospital",
                    lat=13.0830,
                    lon=80.2710,
                    distance_meters=350.0,
                    phone="108",
                ),
                EmergencyServiceItem(
                    id="2",
                    name="Fire Station",
                    category="fire_station",
                    lat=13.0840,
                    lon=80.2720,
                    distance_meters=1200.0,
                    phone="101",
                ),
            ],
            count=2,
            radius_used=5000,
            source="overpass",
        )

        mock_emergency_service.find_nearby = AsyncMock(return_value=mock_result)

        response = test_client.get(
            "/api/v1/emergency/nearby",
            params={"lat": 13.0827, "lon": 80.2707}
        )

        assert response.status_code == 200
        body = response.json()
        data = body.get("data", body)
        assert data["count"] == 2
        assert len(data["services"]) == 2
        assert data["services"][0]["name"] == "City Hospital"

    def test_get_nearby_services_with_categories(self, test_client, mock_emergency_service):
        """Test nearby services with category filter."""
        from models.schemas import EmergencyResponse

        mock_result = EmergencyResponse(
            services=[],
            count=1,
            radius_used=5000,
            source="overpass",
        )

        mock_emergency_service.find_nearby = AsyncMock(return_value=mock_result)

        response = test_client.get(
            "/api/v1/emergency/nearby",
            params={
                "lat": 13.0827,
                "lon": 80.2707,
                "categories": "hospital,pharmacy",
            }
        )

        assert response.status_code == 200
        mock_emergency_service.find_nearby.assert_called_once()
        call_kwargs = mock_emergency_service.find_nearby.call_args[1]
        assert call_kwargs["categories"] == "hospital,pharmacy"

    def test_get_nearby_services_with_radius(self, test_client, mock_emergency_service):
        """Test nearby services with custom radius."""
        from models.schemas import EmergencyResponse

        mock_result = EmergencyResponse(
            services=[],
            count=0,
            radius_used=10000,
            source="overpass",
        )

        mock_emergency_service.find_nearby = AsyncMock(return_value=mock_result)

        response = test_client.get(
            "/api/v1/emergency/nearby",
            params={
                "lat": 13.0827,
                "lon": 80.2707,
                "radius": 10000,
            }
        )

        assert response.status_code == 200
        call_kwargs = mock_emergency_service.find_nearby.call_args[1]
        assert call_kwargs["radius"] == 10000

    def test_get_nearby_services_invalid_coordinates(self, test_client):
        """Test rejection of invalid coordinates."""
        response = test_client.get(
            "/api/v1/emergency/nearby",
            params={"lat": 100.0, "lon": 80.2707}
        )
        assert response.status_code == 422

    def test_get_nearby_services_invalid_radius(self, test_client):
        """Test rejection of invalid radius."""
        response = test_client.get(
            "/api/v1/emergency/nearby",
            params={
                "lat": 13.0827,
                "lon": 80.2707,
                "radius": 50,
            }
        )
        assert response.status_code == 422

    def test_get_nearby_services_external_error(self, test_client, mock_emergency_service):
        """Test handling of external service errors."""
        from services.exceptions import ExternalServiceError

        mock_emergency_service.find_nearby = AsyncMock(
            side_effect=ExternalServiceError("Overpass API unavailable")
        )

        response = test_client.get(
            "/api/v1/emergency/nearby",
            params={"lat": 13.0827, "lon": 80.2707}
        )

        assert response.status_code == 503
        assert "Overpass API unavailable" in response.json()["detail"]


# ── Get SOS Payload Tests ───────────────────────────────────────────────────

class TestGetSOSPayload:
    """Tests for GET /sos endpoint."""

    def test_get_sos_payload_success(self, test_client, mock_emergency_service):
        """Test successful SOS payload generation."""
        from models.schemas import EmergencyNumber, SosResponse

        mock_result = SosResponse(
            services=[],
            count=0,
            radius_used=5000,
            source="overpass",
            numbers={
                "ambulance": EmergencyNumber(service="102", coverage="Pan-India", notes="Public ambulance"),
                "police": EmergencyNumber(service="100", coverage="Pan-India", notes="Police emergency"),
            },
        )

        mock_emergency_service.build_sos_payload = AsyncMock(return_value=mock_result)

        response = test_client.get(
            "/api/v1/emergency/sos",
            params={"lat": 13.0827, "lon": 80.2707}
        )

        assert response.status_code == 200
        body = response.json()
        data = body.get("data", body)
        assert "ambulance" in data["numbers"]
        assert data["radius_used"] == 5000

    def test_get_sos_payload_invalid_coordinates(self, test_client):
        """Test rejection of invalid coordinates."""
        response = test_client.get(
            "/api/v1/emergency/sos",
            params={"lat": 0, "lon": 200}
        )
        assert response.status_code == 422

    def test_get_sos_payload_external_error(self, test_client, mock_emergency_service):
        """Test handling of external service errors."""
        from services.exceptions import ExternalServiceError

        mock_emergency_service.build_sos_payload = AsyncMock(
            side_effect=ExternalServiceError("Service unavailable")
        )

        response = test_client.get(
            "/api/v1/emergency/sos",
            params={"lat": 13.0827, "lon": 80.2707}
        )

        assert response.status_code == 503


# ── Create SOS Incident Tests ───────────────────────────────────────────────

class TestCreateSOSIncident:
    """Tests for POST /sos endpoint."""

    def test_create_sos_incident_success(self, test_client, mock_emergency_service, mock_db_session):
        """Test successful SOS incident creation."""
        from models.schemas import EmergencyNumber, SosResponse

        mock_result = SosResponse(
            services=[],
            count=0,
            radius_used=5000,
            source="overpass",
            numbers={
                "ambulance": EmergencyNumber(service="102", coverage="Pan-India", notes="Public ambulance"),
                "police": EmergencyNumber(service="100", coverage="Pan-India", notes="Police emergency"),
            },
        )

        mock_emergency_service.build_sos_payload = AsyncMock(return_value=mock_result)

        with patch("api.v1.emergency.get_alert_service"), \
             patch("core.audit.AuditLog.log_sos_trigger"):
            response = test_client.post(
                "/api/v1/emergency/sos",
                params={"lat": 13.0827, "lon": 80.2707}
            )

        assert response.status_code == 200
        body = response.json()
        data = body.get("data", body)
        assert data["count"] == 0
        assert "ambulance" in data["numbers"]

    def test_create_sos_incident_with_user(self, test_client, mock_emergency_service, mock_db_session):
        """Test SOS creation with authenticated user."""
        from datetime import datetime, timedelta

        import jwt

        from core.security import ALGORITHM, APP_JWT_AUDIENCE, APP_JWT_ISSUER, SECRET_KEY
        from models.schemas import EmergencyNumber, SosResponse

        mock_result = SosResponse(
            services=[],
            count=0,
            radius_used=5000,
            source="overpass",
            numbers={
                "ambulance": EmergencyNumber(service="102", coverage="Pan-India", notes="Public ambulance"),
            },
        )

        mock_emergency_service.build_sos_payload = AsyncMock(return_value=mock_result)

        token = jwt.encode(
            {
                "sub": "test-user-id",
                "aud": APP_JWT_AUDIENCE,
                "iss": APP_JWT_ISSUER,
                "exp": datetime.now(UTC) + timedelta(hours=1),
            },
            SECRET_KEY,
            algorithm=ALGORITHM,
        )

        with patch("api.v1.emergency.get_alert_service"), \
             patch("core.audit.AuditLog.log_sos_trigger"):
            response = test_client.post(
                "/api/v1/emergency/sos",
                params={"lat": 13.0827, "lon": 80.2707},
                headers={"Authorization": f"Bearer {token}"},
            )

        assert response.status_code == 200

    def test_create_sos_incident_external_error(self, test_client, mock_emergency_service, mock_db_session):
        """Test SOS creation with external service failure."""
        from services.exceptions import ExternalServiceError

        mock_emergency_service.build_sos_payload = AsyncMock(
            side_effect=ExternalServiceError("Service down")
        )

        with patch("api.v1.emergency.get_alert_service"):
            response = test_client.post(
                "/api/v1/emergency/sos",
                params={"lat": 13.0827, "lon": 80.2707}
            )

        assert response.status_code == 503

    def test_create_sos_incident_general_exception(self, test_client, mock_emergency_service, mock_db_session):
        """Test SOS creation with a non-ExternalServiceError triggers general Exception handler (lines 203-212).

        NOTE: ExternalServiceError inherits from RuntimeError, so we use KeyError
        to guarantee the except Exception (not except ExternalServiceError) path.
        """
        mock_emergency_service.build_sos_payload = AsyncMock(
            side_effect=KeyError("Unexpected internal error")
        )

        with patch("api.v1.emergency.get_alert_service"), \
             patch("core.audit.AuditLog.log_sos_trigger"):
            response = test_client.post(
                "/api/v1/emergency/sos",
                params={"lat": 13.0827, "lon": 80.2707}
            )

        assert response.status_code == 503
        mock_db_session.rollback.assert_called_once()

# ── Get Emergency Numbers Tests ─────────────────────────────────────────────

class TestGetEmergencyNumbers:
    """Tests for GET /numbers endpoint."""

    def test_get_emergency_numbers(self, test_client):
        """Test emergency numbers endpoint."""
        response = test_client.get("/api/v1/emergency/numbers")

        assert response.status_code == 200
        body = response.json()
        data = body.get("data", body)
        assert "numbers" in data
        assert "ambulance" in data["numbers"] or "police" in data["numbers"]


# ── Safe Spaces Tests ───────────────────────────────────────────────────────

class TestSafeSpaces:
    """Tests for GET /safe-spaces endpoint."""

    def test_safe_spaces_success(self, test_client):
        """Test safe spaces endpoint."""
        with patch("services.safe_spaces.get_safe_spaces") as mock_safe_spaces:
            mock_safe_spaces.return_value = {
                "spaces": [
                    {
                        "name": "Safe Zone 1",
                        "lat": 13.0830,
                        "lon": 80.2710,
                        "rating": 4.5,
                    }
                ],
                "count": 1,
            }

            response = test_client.get(
                "/api/v1/emergency/safe-spaces",
                params={"lat": 13.0827, "lon": 80.2707}
            )

            assert response.status_code == 200
            body = response.json()
            data = body.get("data", body)
            assert data["count"] == 1

    def test_safe_spaces_invalid_coordinates(self, test_client):
        """Test rejection of invalid coordinates."""
        response = test_client.get(
            "/api/v1/emergency/safe-spaces",
            params={"lat": 100.0, "lon": 80.2707}
        )
        assert response.status_code == 422

    def test_safe_spaces_invalid_radius(self, test_client):
        """Test rejection of invalid radius."""
        response = test_client.get(
            "/api/v1/emergency/safe-spaces",
            params={
                "lat": 13.0827,
                "lon": 80.2707,
                "radius": 50,
            }
        )
        assert response.status_code == 422


# ── Service Dependency Tests ────────────────────────────────────────────────

class TestServiceDependency:
    """Tests for service dependency injection."""

    def test_get_emergency_service(self):
        """Test emergency service dependency."""
        mock_request = MagicMock()
        mock_request.app.state.emergency_service = MagicMock()

        result = emergency.get_emergency_service(mock_request)

        assert result == mock_request.app.state.emergency_service
