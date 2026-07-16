# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def disable_limiter():
    from core.limiter import limiter
    limiter.enabled = False
    yield


def _mock_db_session(result=None, side_effect=None):
    session = AsyncMock()
    if side_effect:
        session.execute = AsyncMock(side_effect=side_effect)
    else:
        session.execute = AsyncMock(return_value=result)
    return session


@pytest.fixture
def wards_app():
    app = FastAPI()
    from api.v1.wards import router
    app.include_router(router)
    return app


@pytest.fixture
def mock_ward():
    ward = MagicMock()
    ward.ward_id = "ward-1"
    ward.ward_name = "Ward 1"
    ward.zone_name = "Zone A"
    ward.city = "Chennai"
    ward.state_code = "TN"
    ward.population = 50000
    ward.area_sqkm = 10.5
    return ward


class TestListWards:
    def test_list_all(self, wards_app, mock_ward):
        with patch("api.v1.wards.WardService.list_all_wards", AsyncMock(return_value=[mock_ward])):
            from api.v1.wards import get_db
            wards_app.dependency_overrides[get_db] = lambda: _mock_db_session()

            client = TestClient(wards_app)
            response = client.get("/api/v1/wards")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["ward_name"] == "Ward 1"

    def test_list_empty(self, wards_app):
        with patch("api.v1.wards.WardService.list_all_wards", AsyncMock(return_value=[])):
            from api.v1.wards import get_db
            wards_app.dependency_overrides[get_db] = lambda: _mock_db_session()

            client = TestClient(wards_app)
            response = client.get("/api/v1/wards")
            assert response.json() == []

    def test_list_multiple(self, wards_app):
        wards = [
            MagicMock(ward_id="w1", ward_name="Ward 1", zone_name="A", city="Chennai", state_code="TN", population=100, area_sqkm=1.0),
            MagicMock(ward_id="w2", ward_name="Ward 2", zone_name="B", city="Chennai", state_code="TN", population=200, area_sqkm=2.0),
        ]
        with patch("api.v1.wards.WardService.list_all_wards", AsyncMock(return_value=wards)):
            from api.v1.wards import get_db
            wards_app.dependency_overrides[get_db] = lambda: _mock_db_session()

            client = TestClient(wards_app)
            response = client.get("/api/v1/wards")
            assert len(response.json()) == 2


class TestLocateWard:
    def test_locate_found(self, wards_app, mock_ward):
        with patch("api.v1.wards.WardService.find_ward_by_coordinates", AsyncMock(return_value=mock_ward)):
            from api.v1.wards import get_db
            wards_app.dependency_overrides[get_db] = lambda: _mock_db_session()

            client = TestClient(wards_app)
            response = client.get("/api/v1/wards/locate?lat=13.0&lon=80.0")
            assert response.status_code == 200
            assert response.json()["ward_id"] == "ward-1"

    def test_locate_not_found(self, wards_app):
        with patch("api.v1.wards.WardService.find_ward_by_coordinates", AsyncMock(return_value=None)):
            from api.v1.wards import get_db
            wards_app.dependency_overrides[get_db] = lambda: _mock_db_session()

            client = TestClient(wards_app)
            response = client.get("/api/v1/wards/locate?lat=0.0&lon=0.0")
            assert response.status_code == 404

    def test_locate_invalid_lat(self, wards_app):
        client = TestClient(wards_app)
        response = client.get("/api/v1/wards/locate?lat=999&lon=80.0")
        assert response.status_code == 422


class TestWardStats:
    def test_stats_success(self, wards_app, mock_ward):
        mock_stats = {
            "ward_id": "ward-1",
            "open_issues": 10,
            "resolved_issues": 20,
            "rejected_issues": 1,
            "total_issues": 31,
            "resolution_rate": 66.67,
        }

        ward_result = MagicMock()
        ward_result.scalar_one_or_none.return_value = mock_ward

        db = _mock_db_session(ward_result)

        from api.v1.wards import get_db
        wards_app.dependency_overrides[get_db] = lambda: db

        with patch("api.v1.wards.WardService.get_ward_stats", AsyncMock(return_value=mock_stats)):
            client = TestClient(wards_app)
            response = client.get("/api/v1/wards/ward-1/stats")
            assert response.status_code == 200
            assert response.json()["resolution_rate"] == 66.67

    def test_stats_ward_not_found(self, wards_app):
        ward_result = MagicMock()
        ward_result.scalar_one_or_none.return_value = None
        db = _mock_db_session(ward_result)

        from api.v1.wards import get_db
        wards_app.dependency_overrides[get_db] = lambda: db

        client = TestClient(wards_app)
        response = client.get("/api/v1/wards/nonexistent/stats")
        assert response.status_code == 404
