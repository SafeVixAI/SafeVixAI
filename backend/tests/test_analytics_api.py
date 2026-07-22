# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def disable_limiter():
    from core.limiter import limiter
    limiter.enabled = False
    yield


def _mock_db_session(execute_result=None, side_effect=None):
    session = AsyncMock()
    if side_effect:
        session.execute = AsyncMock(side_effect=side_effect)
    else:
        session.execute = AsyncMock(return_value=execute_result)
    session.commit = AsyncMock()
    session.add = MagicMock()
    return session


def _analytics_app():
    app = FastAPI()
    from api.v1.analytics import router
    app.include_router(router)
    return app


_MOCK_UUID = uuid.uuid4()


class TestHeatmap:
    def test_heatmap_success(self):
        app = _analytics_app()
        mock_issue = MagicMock()
        mock_issue.uuid = _MOCK_UUID
        mock_issue.category = "pothole"
        mock_issue.severity = 3
        mock_issue.status = "open"
        mock_issue.issue_type = "pothole"

        result = MagicMock()
        result.all.return_value = [(mock_issue, 13.0, 80.0)]
        db = _mock_db_session(result)

        from api.v1.analytics import get_db
        app.dependency_overrides[get_db] = lambda: db

        client = TestClient(app)
        response = client.get("/api/v1/analytics/heatmap")
        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "FeatureCollection"
        assert len(data["features"]) == 1

    def test_heatmap_with_category_filter(self):
        app = _analytics_app()
        mock_issue = MagicMock()
        mock_issue.uuid = _MOCK_UUID
        mock_issue.category = "traffic"
        mock_issue.severity = 2
        mock_issue.status = "open"

        result = MagicMock()
        result.all.return_value = [(mock_issue, 13.1, 80.1)]
        db = _mock_db_session(result)

        from api.v1.analytics import get_db
        app.dependency_overrides[get_db] = lambda: db

        client = TestClient(app)
        response = client.get("/api/v1/analytics/heatmap?category=traffic")
        assert response.status_code == 200

    def test_heatmap_empty(self):
        app = _analytics_app()
        result = MagicMock()
        result.all.return_value = []
        db = _mock_db_session(result)

        from api.v1.analytics import get_db
        app.dependency_overrides[get_db] = lambda: db

        client = TestClient(app)
        response = client.get("/api/v1/analytics/heatmap")
        assert response.status_code == 200
        assert response.json()["features"] == []


class TestWardSummary:
    def test_ward_summary_success(self):
        app = _analytics_app()
        row = MagicMock()
        row.ward_id = "ward-1"
        row.ward_name = "Ward 1"
        row.zone_name = "Zone A"
        row.open_count = 5
        row.resolved_count = 10
        row.rejected_count = 1
        row.breached_count = 2

        result = MagicMock()
        result.all.return_value = [row]
        db = _mock_db_session(result)

        from api.v1.analytics import get_db

        with patch("api.v1.analytics.WardService.ensure_seeded", AsyncMock()):
            app.dependency_overrides[get_db] = lambda: db
            client = TestClient(app)
            response = client.get("/api/v1/analytics/ward-summary")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["ward_name"] == "Ward 1"

    def test_ward_summary_zero_total(self):
        app = _analytics_app()
        row = MagicMock()
        row.ward_id = "ward-2"
        row.ward_name = "Ward 2"
        row.zone_name = "Zone B"
        row.open_count = 0
        row.resolved_count = 0
        row.rejected_count = 0
        row.breached_count = 0

        result = MagicMock()
        result.all.return_value = [row]
        db = _mock_db_session(result)

        from api.v1.analytics import get_db

        with patch("api.v1.analytics.WardService.ensure_seeded", AsyncMock()):
            app.dependency_overrides[get_db] = lambda: db
            client = TestClient(app)
            response = client.get("/api/v1/analytics/ward-summary")
            assert response.status_code == 200
            assert response.json()[0]["resolution_rate"] == 0.0

    def test_ward_summary_multiple_wards(self):
        app = _analytics_app()
        rows = [
            MagicMock(ward_id="w1", ward_name="Ward 1", zone_name="A", open_count=1, resolved_count=2, rejected_count=0, breached_count=0),
            MagicMock(ward_id="w2", ward_name="Ward 2", zone_name="B", open_count=3, resolved_count=1, rejected_count=1, breached_count=1),
        ]
        result = MagicMock()
        result.all.return_value = rows
        db = _mock_db_session(result)

        from api.v1.analytics import get_db

        with patch("api.v1.analytics.WardService.ensure_seeded", AsyncMock()):
            app.dependency_overrides[get_db] = lambda: db
            client = TestClient(app)
            response = client.get("/api/v1/analytics/ward-summary")
            assert len(response.json()) == 2


class TestSLABreach:
    def test_sla_breach_success(self):
        app = _analytics_app()
        issue = MagicMock()
        issue.uuid = _MOCK_UUID
        issue.issue_type = "pothole"
        issue.severity = 4
        issue.description = "Breached SLA"
        issue.location_address = "Main Road"
        issue.road_name = "Main Road"
        issue.road_type = "arterial"
        issue.road_number = ""
        issue.authority_name = "PWD"
        issue.status = "open"
        issue.created_at = datetime(2026, 1, 1)
        issue.category = "pothole"
        issue.sub_category = None
        issue.ward_id = "ward-1"
        issue.ward_name = "Ward 1"
        issue.assigned_officer_id = None
        issue.sla_deadline = datetime.now(UTC).replace(tzinfo=None) - timedelta(hours=2)
        issue.resolved_at = None
        issue.duplicate_of_uuid = None
        issue.confirmation_count = 0
        issue.before_photo_url = None
        issue.after_photo_url = None

        result = MagicMock()
        result.all.return_value = [(issue, 13.0, 80.0)]
        db = _mock_db_session(result)

        from api.v1.analytics import get_db
        app.dependency_overrides[get_db] = lambda: db

        client = TestClient(app)
        response = client.get("/api/v1/analytics/sla-breach")
        assert response.status_code == 200

    def test_sla_breach_empty(self):
        app = _analytics_app()
        result = MagicMock()
        result.all.return_value = []
        db = _mock_db_session(result)

        from api.v1.analytics import get_db
        app.dependency_overrides[get_db] = lambda: db

        client = TestClient(app)
        response = client.get("/api/v1/analytics/sla-breach")
        assert response.status_code == 200
        assert response.json() == []


class TestCategoryBreakdown:
    def test_category_breakdown(self):
        app = _analytics_app()
        row1 = ("roads", 10)
        row2 = ("traffic", 5)
        row3 = ("streetlight", 3)

        result = MagicMock()
        result.all.return_value = [row1, row2, row3]
        db = _mock_db_session(result)

        from api.v1.analytics import get_db
        app.dependency_overrides[get_db] = lambda: db

        client = TestClient(app)
        response = client.get("/api/v1/analytics/category-breakdown")
        assert response.status_code == 200
        data = response.json()
        assert data["roads"] == 10
        assert data["traffic"] == 5
        assert data["streetlight"] == 3

    def test_category_breakdown_ignores_unknown(self):
        app = _analytics_app()
        row1 = ("roads", 10)
        row2 = ("unknown_cat", 99)

        result = MagicMock()
        result.all.return_value = [row1, row2]
        db = _mock_db_session(result)

        from api.v1.analytics import get_db
        app.dependency_overrides[get_db] = lambda: db

        client = TestClient(app)
        response = client.get("/api/v1/analytics/category-breakdown")
        data = response.json()
        assert data["roads"] == 10
        assert "unknown_cat" not in data

    def test_category_breakdown_empty(self):
        app = _analytics_app()
        result = MagicMock()
        result.all.return_value = []
        db = _mock_db_session(result)

        from api.v1.analytics import get_db
        app.dependency_overrides[get_db] = lambda: db

        client = TestClient(app)
        response = client.get("/api/v1/analytics/category-breakdown")
        data = response.json()
        assert data["roads"] == 0
        assert data["traffic"] == 0
        assert data["streetlight"] == 0
