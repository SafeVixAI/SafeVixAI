# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

from fastapi import status
from fastapi.testclient import TestClient


def test_challan_dispute_endpoint(app) -> None:
    with TestClient(app) as client:
        payload = {
            "challan_ref": "CH-2026-9876",
            "violation_code": "183",
            "fine_amount": 2000,
            "mitigating_factors": "Speed sign was completely obscured by overgrown trees, making visibility impossible."
        }
        response = client.post("/api/v1/challan/dispute", json=payload)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()["data"]
        assert "dispute_ref" in data
        assert "appeal_letter" in data
        assert "Section 183" in data["appeal_letter"]
        assert data["confidence_score"] == 0.92
        assert len(data["cited_mva_sections"]) == 1
        assert data["cited_mva_sections"][0] == "Section 183"


def test_fine_prediction_endpoint(app) -> None:
    with TestClient(app) as client:
        payload = {
            "vehicle_number": "TN-01-AB-1234",
            "state_code": "TN",
            "telemetry": {
                "speeding_events": 5,
                "harsh_braking_events": 2,
                "night_driving_minutes": 180,
                "total_km_driven": 1500.5
            }
        }
        response = client.post("/api/v1/challan/predict", json=payload)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()["data"]
        assert "risk_score" in data
        assert data["risk_level"] == "high"
        assert data["predicted_violations_count"] == 6
        assert data["estimated_annual_liability"] == 30000
        assert len(data["recommendations"]) > 0


def test_garage_sync_unauthorized(app) -> None:
    with TestClient(app) as client:
        # Requests without Authorization should fail with 401
        response = client.post("/api/v1/garage/sync?vehicle_number=TN-01-AB-1234")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_garage_sync_authorized(app, auth_headers) -> None:
    with TestClient(app) as client:
        # Requests with Authorization should succeed
        response = client.post(
            "/api/v1/garage/sync?vehicle_number=TN-01-AB-1234",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()["data"]
        assert data["sync_status"] == "COMPLETED"
        assert len(data["vehicles"]) == 1
        assert data["vehicles"][0]["vehicle_number"] == "TN-01-AB-1234"
        assert data["vehicles"][0]["owner_name"] == "Citizen Appellant"

