# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team
"""Comprehensive civic_intel API coverage tests."""

from __future__ import annotations

import json
from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_async_session
from core.limiter import limiter
from core.rbac import Role, require_role
from core.security import get_current_user

# ──────────────────────────────────────────────────────────
# Shared helpers
# ──────────────────────────────────────────────────────────


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


def _make_session(db):
    """Async-generator factory override for get_async_session."""

    async def _inner():
        yield db

    return _inner


def _admin_user():
    return {"sub": "admin-user", "role": "operator"}


# ══════════════════════════════════════════════════════════════════════════════
# BOUNDARIES
# ══════════════════════════════════════════════════════════════════════════════


class TestBoundaries:
    def test_boundaries_no_filter_empty(self):
        """No state_code filter; empty FeatureCollection returned."""
        from api.v1.civic_intel import router

        db = _mock_db(rows=[])
        app = _mkapp(router)
        app.dependency_overrides[get_async_session] = _make_session(db)
        resp = TestClient(app).get("/civic/boundaries")
        assert resp.status_code == 200
        data = resp.json()
        assert data["type"] == "FeatureCollection"
        assert data["features"] == []

    def test_boundaries_with_state_code_accepted(self):
        """state_code query param accepted; endpoint returns 200."""
        from api.v1.civic_intel import router

        db = _mock_db(rows=[])
        app = _mkapp(router)
        app.dependency_overrides[get_async_session] = _make_session(db)
        resp = TestClient(app).get("/civic/boundaries", params={"state_code": "tn"})
        assert resp.status_code == 200
        assert resp.json()["features"] == []

    def test_boundaries_row_with_geojson_parsed(self):
        """Row with geojson string returns parsed geometry dict."""
        from api.v1.civic_intel import router

        row = MagicMock()
        row.id = 1
        row.code = "TN"
        row.name = "Tamil Nadu"
        row.state_code = "TN"
        row.area_sqkm = 130058.0
        row.geojson = '{"type":"Polygon","coordinates":[]}'
        db = _mock_db(rows=[row])
        app = _mkapp(router)
        app.dependency_overrides[get_async_session] = _make_session(db)
        resp = TestClient(app).get("/civic/boundaries")
        assert resp.status_code == 200
        features = resp.json()["features"]
        assert len(features) == 1
        assert features[0]["type"] == "Feature"
        assert features[0]["geometry"]["type"] == "Polygon"
        assert features[0]["properties"]["code"] == "TN"
        assert features[0]["properties"]["state_code"] == "TN"

    def test_boundaries_row_geojson_none_returns_null_geometry(self):
        """Row with geojson=None returns geometry: null in feature."""
        from api.v1.civic_intel import router

        row = MagicMock()
        row.id = 2
        row.code = "AP"
        row.name = "Andhra Pradesh"
        row.state_code = "AP"
        row.area_sqkm = 162970.0
        row.geojson = None
        db = _mock_db(rows=[row])
        app = _mkapp(router)
        app.dependency_overrides[get_async_session] = _make_session(db)
        resp = TestClient(app).get("/civic/boundaries")
        assert resp.status_code == 200
        assert resp.json()["features"][0]["geometry"] is None


# ══════════════════════════════════════════════════════════════════════════════
# BOUNDARY POINT LOOKUP
# ══════════════════════════════════════════════════════════════════════════════


class TestBoundaryContains:
    def test_contains_returns_matching_boundaries(self):
        """Point lookup returns lat/lon echoed back plus matched boundaries."""
        from api.v1.civic_intel import router

        row = MagicMock()
        row.level = "district"
        row.code = "TN-CHE"
        row.name = "Chennai"
        row.state_code = "TN"
        db = _mock_db(rows=[row])
        app = _mkapp(router)
        app.dependency_overrides[get_async_session] = _make_session(db)
        resp = TestClient(app).get(
            "/civic/boundaries/contains", params={"lat": 13.08, "lon": 80.27}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["lat"] == 13.08
        assert data["lon"] == 80.27
        assert len(data["boundaries"]) == 1
        b = data["boundaries"][0]
        assert b["name"] == "Chennai"
        assert b["level"] == "district"
        assert b["state_code"] == "TN"

    def test_contains_no_boundaries_found(self):
        """Point outside all boundaries returns empty list."""
        from api.v1.civic_intel import router

        db = _mock_db(rows=[])
        app = _mkapp(router)
        app.dependency_overrides[get_async_session] = _make_session(db)
        resp = TestClient(app).get("/civic/boundaries/contains", params={"lat": 0.0, "lon": 0.0})
        assert resp.status_code == 200
        assert resp.json()["boundaries"] == []


# ══════════════════════════════════════════════════════════════════════════════
# LGD LOOKUP
# ══════════════════════════════════════════════════════════════════════════════


class TestLGDLookup:
    def _app(self, scalars_return):
        from api.v1.civic_intel import router

        db = _mock_db()
        db.execute.return_value.scalars.return_value.all.return_value = scalars_return
        app = _mkapp(router)
        app.dependency_overrides[get_async_session] = _make_session(db)
        return app

    def test_lgd_no_filters_empty(self):
        """No filters; empty result returned."""
        app = self._app([])
        resp = TestClient(app).get("/civic/lgd/lookup")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 0
        assert data["entities"] == []

    def test_lgd_with_q_filter_returns_entity(self):
        """Search term q filter returns matching entities."""
        e = MagicMock()
        e.lgd_code = 101
        e.entity_type = "district"
        e.name_en = "Chennai"
        e.name_local = "சென்னை"
        e.state_code = "TN"
        e.parent_lgd_code = 33
        e.census_code_2011 = "601"
        e.population_census_2011 = 7088000
        app = self._app([e])
        resp = TestClient(app).get("/civic/lgd/lookup", params={"q": "Chennai"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 1
        assert data["entities"][0]["name_en"] == "Chennai"
        assert data["entities"][0]["lgd_code"] == 101

    def test_lgd_with_entity_type_filter(self):
        """entity_type filter is applied; empty result OK."""
        app = self._app([])
        resp = TestClient(app).get("/civic/lgd/lookup", params={"entity_type": "block"})
        assert resp.status_code == 200
        assert resp.json()["count"] == 0

    def test_lgd_with_state_code_uppercased(self):
        """state_code is upper-cased before filtering."""
        app = self._app([])
        resp = TestClient(app).get("/civic/lgd/lookup", params={"state_code": "tn"})
        assert resp.status_code == 200

    def test_lgd_with_lgd_code_filter(self):
        """lgd_code integer filter applied."""
        app = self._app([])
        resp = TestClient(app).get("/civic/lgd/lookup", params={"lgd_code": 101})
        assert resp.status_code == 200


# ══════════════════════════════════════════════════════════════════════════════
# LGD HIERARCHY
# ══════════════════════════════════════════════════════════════════════════════


class TestLGDHierarchy:
    def test_hierarchy_groups_entities_by_type(self):
        """Entities are keyed by entity_type in the returned hierarchy."""
        from api.v1.civic_intel import router

        e1 = MagicMock()
        e1.entity_type = "district"
        e1.lgd_code = 101
        e1.name_en = "Chennai"
        e1.parent_lgd_code = 33
        e2 = MagicMock()
        e2.entity_type = "district"
        e2.lgd_code = 102
        e2.name_en = "Coimbatore"
        e2.parent_lgd_code = 33
        db = _mock_db()
        db.execute.return_value.scalars.return_value.all.return_value = [e1, e2]
        app = _mkapp(router)
        app.dependency_overrides[get_async_session] = _make_session(db)
        resp = TestClient(app).get("/civic/lgd/hierarchy", params={"state_code": "TN"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["state_code"] == "TN"
        assert "district" in data["hierarchy"]
        assert len(data["hierarchy"]["district"]) == 2

    def test_hierarchy_empty_state_returns_empty_dict(self):
        """No entities for the state returns empty hierarchy."""
        from api.v1.civic_intel import router

        db = _mock_db()
        db.execute.return_value.scalars.return_value.all.return_value = []
        app = _mkapp(router)
        app.dependency_overrides[get_async_session] = _make_session(db)
        resp = TestClient(app).get("/civic/lgd/hierarchy", params={"state_code": "XX"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["state_code"] == "XX"
        assert data["hierarchy"] == {}


# ══════════════════════════════════════════════════════════════════════════════
# OSM CIVIC FEATURES — NEARBY
# ══════════════════════════════════════════════════════════════════════════════


class TestNearbyFeatures:
    def test_nearby_no_feature_type_returns_empty(self):
        """Without feature_type filter; empty result returned."""
        from api.v1.civic_intel import router

        db = _mock_db(rows=[])
        app = _mkapp(router)
        app.dependency_overrides[get_async_session] = _make_session(db)
        resp = TestClient(app).get("/civic/features/nearby", params={"lat": 13.08, "lon": 80.27})
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 0
        assert data["features"] == []

    def test_nearby_with_feature_type_returns_row(self):
        """feature_type filter; row fields correctly mapped."""
        from api.v1.civic_intel import router

        row = MagicMock()
        row.id = 1
        row.osm_id = "123456"
        row.feature_type = "hospital"
        row.city = "Chennai"
        row.lat = 13.08
        row.lon = 80.27
        row.distance_m = 250.5
        row.tags_json = {"name": "Apollo Hospital"}
        db = _mock_db(rows=[row])
        app = _mkapp(router)
        app.dependency_overrides[get_async_session] = _make_session(db)
        resp = TestClient(app).get(
            "/civic/features/nearby",
            params={"lat": 13.08, "lon": 80.27, "feature_type": "hospital"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 1
        f = data["features"][0]
        assert f["feature_type"] == "hospital"
        assert f["city"] == "Chennai"
        assert f["distance_m"] == 250.5

    def test_nearby_distance_m_none_serialized_as_null(self):
        """Row where distance_m is None → distance_m: null in response."""
        from api.v1.civic_intel import router

        row = MagicMock()
        row.id = 2
        row.osm_id = "789"
        row.feature_type = "school"
        row.city = "Madurai"
        row.lat = 9.9
        row.lon = 78.1
        row.distance_m = None
        row.tags_json = {}
        db = _mock_db(rows=[row])
        app = _mkapp(router)
        app.dependency_overrides[get_async_session] = _make_session(db)
        resp = TestClient(app).get("/civic/features/nearby", params={"lat": 9.9, "lon": 78.1})
        assert resp.status_code == 200
        assert resp.json()["features"][0]["distance_m"] is None


# ══════════════════════════════════════════════════════════════════════════════
# OSM CIVIC FEATURES — HEATMAP
# ══════════════════════════════════════════════════════════════════════════════


class TestFeatureHeatmap:
    def test_heatmap_rows_with_avg_lat_included_in_clusters(self):
        """Rows with avg_lat truthy are included; values cast to float."""
        from api.v1.civic_intel import router

        row = MagicMock()
        row.city = "Chennai"
        row.count = 15
        row.avg_lat = 13.08
        row.avg_lon = 80.27
        db = _mock_db(rows=[row])
        app = _mkapp(router)
        app.dependency_overrides[get_async_session] = _make_session(db)
        resp = TestClient(app).get("/civic/features/heatmap", params={"feature_type": "hospital"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["feature_type"] == "hospital"
        assert len(data["clusters"]) == 1
        c = data["clusters"][0]
        assert c["city"] == "Chennai"
        assert c["count"] == 15
        assert c["lat"] == 13.08

    def test_heatmap_rows_without_avg_lat_filtered_out(self):
        """Rows where avg_lat is None/falsy are excluded from clusters."""
        from api.v1.civic_intel import router

        row = MagicMock()
        row.city = "Unknown"
        row.count = 5
        row.avg_lat = None
        row.avg_lon = None
        db = _mock_db(rows=[row])
        app = _mkapp(router)
        app.dependency_overrides[get_async_session] = _make_session(db)
        resp = TestClient(app).get("/civic/features/heatmap", params={"feature_type": "school"})
        assert resp.status_code == 200
        assert resp.json()["clusters"] == []


# ══════════════════════════════════════════════════════════════════════════════
# GOV DATASETS
# ══════════════════════════════════════════════════════════════════════════════


class TestDatasets:
    def _app_with_records(self, records):
        from api.v1.civic_intel import router

        db = _mock_db()
        db.execute.return_value.scalars.return_value.all.return_value = records
        app = _mkapp(router)
        app.dependency_overrides[get_async_session] = _make_session(db)
        return app

    def test_datasets_no_filters_empty(self):
        """No filters returns empty record set."""
        app = self._app_with_records([])
        resp = TestClient(app).get("/civic/datasets")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 0
        assert data["records"] == []

    def test_datasets_with_slug_returns_record(self):
        """Slug filter; all record fields serialized."""
        r = MagicMock()
        r.id = 1
        r.dataset_slug = "road-accidents"
        r.year = 2023
        r.state_code = "TN"
        r.district_name = "Chennai"
        r.metric_name = "total_accidents"
        r.metric_value = 500
        r.unit = "count"
        r.data_json = {"source": "NCRB"}
        app = self._app_with_records([r])
        resp = TestClient(app).get("/civic/datasets", params={"slug": "road-accidents"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 1
        assert data["records"][0]["dataset_slug"] == "road-accidents"
        assert data["records"][0]["year"] == 2023

    def test_datasets_with_state_code_and_year(self):
        """state_code uppercased and year filter; empty result OK."""
        app = self._app_with_records([])
        resp = TestClient(app).get("/civic/datasets", params={"state_code": "mh", "year": 2022})
        assert resp.status_code == 200
        assert resp.json()["count"] == 0


# ══════════════════════════════════════════════════════════════════════════════
# GRIEVANCES
# ══════════════════════════════════════════════════════════════════════════════


class TestGrievances:
    def _app_with_grievances(self, rows):
        from api.v1.civic_intel import router

        db = _mock_db()
        db.execute.return_value.scalars.return_value.all.return_value = rows
        app = _mkapp(router)
        app.dependency_overrides[get_async_session] = _make_session(db)
        return app

    def test_grievances_no_filters_empty(self):
        """No filters returns empty grievances list."""
        app = self._app_with_grievances([])
        resp = TestClient(app).get("/civic/grievances")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 0
        assert data["grievances"] == []

    def test_grievances_all_filters_applied(self):
        """All filters (source, category, state_code, status) accepted."""
        app = self._app_with_grievances([])
        resp = TestClient(app).get(
            "/civic/grievances",
            params={"source": "cpgrams", "category": "water", "state_code": "tn", "status": "open"},
        )
        assert resp.status_code == 200

    def test_grievances_filed_at_none_serialized_as_null(self):
        """filed_at=None and resolved_at=None → null in JSON."""
        g = MagicMock()
        g.id = 1
        g.source = "cpgrams"
        g.grievance_ref = "GR-001"
        g.category = "water"
        g.subcategory = "pipe_burst"
        g.description = "No water supply for 3 days"
        g.state_code = "TN"
        g.complainant_district = "Chennai"
        g.status = "open"
        g.filed_at = None
        g.resolved_at = None
        app = self._app_with_grievances([g])
        resp = TestClient(app).get("/civic/grievances")
        assert resp.status_code == 200
        grievance = resp.json()["grievances"][0]
        assert grievance["filed_at"] is None
        assert grievance["resolved_at"] is None
        assert grievance["category"] == "water"

    def test_grievances_filed_at_set_uses_isoformat(self):
        """Real datetime values are serialized with isoformat()."""
        g = MagicMock()
        g.id = 2
        g.source = "cpgrams"
        g.grievance_ref = "GR-002"
        g.category = "sanitation"
        g.subcategory = None
        g.description = "Garbage not collected for a week in the area"
        g.state_code = "MH"
        g.complainant_district = "Mumbai"
        g.status = "resolved"
        g.filed_at = datetime(2024, 1, 15, 10, 30, tzinfo=timezone.utc)
        g.resolved_at = datetime(2024, 1, 20, 12, 0, tzinfo=timezone.utc)
        app = self._app_with_grievances([g])
        resp = TestClient(app).get("/civic/grievances")
        assert resp.status_code == 200
        grievance = resp.json()["grievances"][0]
        assert "2024-01-15" in grievance["filed_at"]
        assert grievance["resolved_at"] is not None


# ══════════════════════════════════════════════════════════════════════════════
# CIVIC STATS (5 sequential DB calls)
# ══════════════════════════════════════════════════════════════════════════════


class TestCivicStats:
    @staticmethod
    def _scalar_r(value):
        r = MagicMock()
        r.scalar.return_value = value
        return r

    @staticmethod
    def _all_r(rows):
        r = MagicMock()
        r.all.return_value = rows
        return r

    def test_stats_no_state_code_five_db_calls(self):
        """Global stats without state_code — 5 sequential execute calls."""
        from api.v1.civic_intel import router

        db = _mock_db()
        db.execute.side_effect = [
            self._scalar_r(100),  # lgd_count
            self._scalar_r(50),  # boundary_count
            self._all_r([]),  # osm_counts (empty)
            self._all_r([]),  # grv_counts (empty)
            self._scalar_r(20),  # muni_count
        ]
        app = _mkapp(router)
        app.dependency_overrides[get_async_session] = _make_session(db)
        resp = TestClient(app).get("/civic/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert data["lgd_entities"] == 100
        assert data["admin_boundaries"] == 50
        assert data["municipalities"] == 20
        assert data["state_code"] is None
        assert data["osm_features"] == {}
        assert data["grievances"] == {}

    def test_stats_with_state_code_filters_and_aggregations(self):
        """state_code-filtered stats with populated aggregations."""
        from api.v1.civic_intel import router

        db = _mock_db()
        db.execute.side_effect = [
            self._scalar_r(30),  # lgd
            self._scalar_r(15),  # boundaries
            self._all_r([("hospital", 80), ("school", 40)]),  # osm features
            self._all_r([("water", 40), ("road", 20)]),  # grievances
            self._scalar_r(5),  # municipalities
        ]
        app = _mkapp(router)
        app.dependency_overrides[get_async_session] = _make_session(db)
        resp = TestClient(app).get("/civic/stats", params={"state_code": "TN"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["state_code"] == "TN"
        assert data["lgd_entities"] == 30
        assert data["admin_boundaries"] == 15
        assert data["osm_features"] == {"hospital": 80, "school": 40}
        assert data["grievances"] == {"water": 40, "road": 20}
        assert data["municipalities"] == 5

    def test_stats_scalar_none_defaults_to_zero(self):
        """scalar() returning None → field defaults to 0."""
        from api.v1.civic_intel import router

        db = _mock_db()
        db.execute.side_effect = [
            self._scalar_r(None),  # lgd_count (None → 0)
            self._scalar_r(None),  # boundary_count (None → 0)
            self._all_r([]),
            self._all_r([]),
            self._scalar_r(None),  # muni_count (None → 0)
        ]
        app = _mkapp(router)
        app.dependency_overrides[get_async_session] = _make_session(db)
        resp = TestClient(app).get("/civic/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert data["lgd_entities"] == 0
        assert data["municipalities"] == 0


# ══════════════════════════════════════════════════════════════════════════════
# MUNICIPALITIES — LIST
# ══════════════════════════════════════════════════════════════════════════════


class TestListMunicipalities:
    def _app_with_results(self, total, items):
        from api.v1.civic_intel import router

        db = _mock_db()
        count_r = MagicMock()
        count_r.scalar.return_value = total
        items_r = MagicMock()
        items_r.scalars.return_value = items_r
        items_r.all.return_value = items
        db.execute.side_effect = [count_r, items_r]
        app = _mkapp(router)
        app.dependency_overrides[get_async_session] = _make_session(db)
        return app

    def test_list_no_filters_empty(self):
        """No filters; returns total=0 and empty list."""
        app = self._app_with_results(0, [])
        resp = TestClient(app).get("/civic/municipalities")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["municipalities"] == []

    def test_list_with_q_filter_returns_municipality(self):
        """Search term q returns municipality with all fields."""
        m = MagicMock()
        m.slug = "gcc"
        m.name = "Greater Chennai Corporation"
        m.short_name = "GCC"
        m.municipality_type = "corporation"
        m.city = "Chennai"
        m.state_code = "TN"
        m.state_name = "Tamil Nadu"
        m.ward_count = 200
        m.population = 7088000
        m.helpline_phone = "1913"
        app = self._app_with_results(1, [m])
        resp = TestClient(app).get("/civic/municipalities", params={"q": "Chennai"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["municipalities"][0]["slug"] == "gcc"
        assert data["municipalities"][0]["helpline_phone"] == "1913"

    def test_list_with_state_code_and_municipality_type(self):
        """state_code uppercased and municipality_type filter applied."""
        app = self._app_with_results(0, [])
        resp = TestClient(app).get(
            "/civic/municipalities", params={"state_code": "mh", "municipality_type": "corporation"}
        )
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    def test_list_count_none_defaults_to_zero(self):
        """count scalar returning None → total defaults to 0."""
        from api.v1.civic_intel import router

        db = _mock_db()
        count_r = MagicMock()
        count_r.scalar.return_value = None  # None → 0 via `or 0`
        items_r = MagicMock()
        items_r.scalars.return_value = items_r
        items_r.all.return_value = []
        db.execute.side_effect = [count_r, items_r]
        app = _mkapp(router)
        app.dependency_overrides[get_async_session] = _make_session(db)
        resp = TestClient(app).get("/civic/municipalities")
        assert resp.status_code == 200
        assert resp.json()["total"] == 0


# ══════════════════════════════════════════════════════════════════════════════
# MUNICIPALITIES — NEARBY
# ══════════════════════════════════════════════════════════════════════════════


class TestNearbyMunicipality:
    def test_nearby_returns_distance_km_rounded(self):
        """Nearby endpoint returns municipalities with distance_km computed."""
        from api.v1.civic_intel import router

        m = MagicMock()
        m.slug = "gcc"
        m.name = "Greater Chennai Corporation"
        m.city = "Chennai"
        m.state_code = "TN"
        db = _mock_db()
        db.execute.return_value.all.return_value = [(m, 1500.0)]
        app = _mkapp(router)
        app.dependency_overrides[get_async_session] = _make_session(db)
        resp = TestClient(app).get(
            "/civic/municipalities/nearby", params={"lat": 13.08, "lon": 80.27}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["lat"] == 13.08
        assert data["lon"] == 80.27
        assert len(data["municipalities"]) == 1
        entry = data["municipalities"][0]
        assert entry["slug"] == "gcc"
        assert entry["distance_km"] == 1.5  # round(1500/1000, 1)


# ══════════════════════════════════════════════════════════════════════════════
# MUNICIPALITIES — GET (single)
# ══════════════════════════════════════════════════════════════════════════════


class TestGetMunicipality:
    def _mock_full_municipality(self):
        m = MagicMock()
        m.slug = "gcc"
        m.name = "Greater Chennai Corporation"
        m.short_name = "GCC"
        m.municipality_type = "corporation"
        m.city = "Chennai"
        m.state_code = "TN"
        m.state_name = "Tamil Nadu"
        m.lgd_code = 12345
        m.district_name = "Chennai"
        m.headquarters_address = "1 Ripon Building, Chennai"
        m.helpline_phone = "1913"
        m.whatsapp_number = None
        m.email = "gcc@tn.gov.in"
        m.website_url = "https://chennaicorporation.gov.in"
        m.app_name = "GCC App"
        m.app_url = None
        m.grievance_portal_url = None
        m.mayor_name = "Mayor Name"
        m.mayor_photo_url = None
        m.commissioner_name = "Commissioner Name"
        m.commissioner_phone = None
        m.ward_count = 200
        m.population = 7088000
        m.area_sqkm = 426.0
        m.centroid_lat = 13.08
        m.centroid_lon = 80.27
        m.description = "Largest ULB in Tamil Nadu"
        m.services_offered = ["water", "sanitation", "roads"]
        m.last_verified = None
        return m

    def test_municipality_found_returns_full_profile(self):
        """Known slug returns full structured response."""
        from api.v1.civic_intel import router

        m = self._mock_full_municipality()
        db = _mock_db()
        db.execute.return_value.scalar_one_or_none.return_value = m
        app = _mkapp(router)
        app.dependency_overrides[get_async_session] = _make_session(db)
        resp = TestClient(app).get("/civic/municipalities/gcc")
        assert resp.status_code == 200
        data = resp.json()
        assert data["slug"] == "gcc"
        assert data["contact"]["helpline_phone"] == "1913"
        assert data["leadership"]["mayor_name"] == "Mayor Name"
        assert data["stats"]["ward_count"] == 200
        assert data["geo"]["centroid_lat"] == 13.08
        assert data["last_verified"] is None

    def test_municipality_not_found_returns_404(self):
        """Unknown slug raises 404."""
        from api.v1.civic_intel import router

        db = _mock_db()
        db.execute.return_value.scalar_one_or_none.return_value = None
        app = _mkapp(router)
        app.dependency_overrides[get_async_session] = _make_session(db)
        resp = TestClient(app).get("/civic/municipalities/nonexistent-slug")
        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"].lower()

    def test_municipality_last_verified_set_uses_isoformat(self):
        """last_verified date serialized via isoformat()."""
        from api.v1.civic_intel import router

        m = self._mock_full_municipality()
        m.last_verified = date(2024, 6, 1)
        db = _mock_db()
        db.execute.return_value.scalar_one_or_none.return_value = m
        app = _mkapp(router)
        app.dependency_overrides[get_async_session] = _make_session(db)
        resp = TestClient(app).get("/civic/municipalities/gcc")
        assert resp.status_code == 200
        assert resp.json()["last_verified"] == "2024-06-01"


# ══════════════════════════════════════════════════════════════════════════════
# MUNICIPALITIES — STATS
# ══════════════════════════════════════════════════════════════════════════════


class TestGetMunicipalityStats:
    def test_stats_not_found_returns_404(self):
        """Unknown slug returns 404."""
        from api.v1.civic_intel import router

        db = _mock_db()
        db.execute.return_value.scalar_one_or_none.return_value = None
        app = _mkapp(router)
        app.dependency_overrides[get_async_session] = _make_session(db)
        resp = TestClient(app).get("/civic/municipalities/ghost/stats")
        assert resp.status_code == 404

    def test_stats_found_with_data(self):
        """Municipality found; grievances and infrastructure returned."""
        from api.v1.civic_intel import router

        m = MagicMock()
        m.state_code = "TN"
        m.city = "Chennai"
        r1 = MagicMock()
        r1.scalar_one_or_none.return_value = m
        r2 = MagicMock()
        r2.all.return_value = [("water", "open", 10), ("road", "resolved", 5)]
        r3 = MagicMock()
        r3.all.return_value = [("hospital", 12)]
        db = _mock_db()
        db.execute.side_effect = [r1, r2, r3]
        app = _mkapp(router)
        app.dependency_overrides[get_async_session] = _make_session(db)
        resp = TestClient(app).get("/civic/municipalities/gcc/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert data["slug"] == "gcc"
        assert data["city"] == "Chennai"
        assert len(data["grievances"]) == 2
        assert data["grievances"][0] == {"category": "water", "status": "open", "count": 10}
        assert data["infrastructure"] == {"hospital": 12}

    def test_stats_empty_grievances_and_osm(self):
        """Municipality found but no grievances or OSM data."""
        from api.v1.civic_intel import router

        m = MagicMock()
        m.state_code = "AP"
        m.city = "Vijayawada"
        r1 = MagicMock()
        r1.scalar_one_or_none.return_value = m
        r2 = MagicMock()
        r2.all.return_value = []
        r3 = MagicMock()
        r3.all.return_value = []
        db = _mock_db()
        db.execute.side_effect = [r1, r2, r3]
        app = _mkapp(router)
        app.dependency_overrides[get_async_session] = _make_session(db)
        resp = TestClient(app).get("/civic/municipalities/vmc/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert data["grievances"] == []
        assert data["infrastructure"] == {}


# ══════════════════════════════════════════════════════════════════════════════
# MUNICIPALITIES — WARDS
# ══════════════════════════════════════════════════════════════════════════════


class TestGetMunicipalityWards:
    def test_wards_not_found_returns_404(self):
        """Unknown slug returns 404."""
        from api.v1.civic_intel import router

        db = _mock_db()
        db.execute.return_value.scalar_one_or_none.return_value = None
        app = _mkapp(router)
        app.dependency_overrides[get_async_session] = _make_session(db)
        resp = TestClient(app).get("/civic/municipalities/ghost/wards")
        assert resp.status_code == 404

    def test_wards_found_no_ward_features(self):
        """Municipality found; no ward features returns empty FeatureCollection."""
        from api.v1.civic_intel import router

        m = MagicMock()
        m.short_name = "GCC"
        m.ward_count = 200
        r1 = MagicMock()
        r1.scalar_one_or_none.return_value = m
        r2 = MagicMock()
        r2.all.return_value = []
        db = _mock_db()
        db.execute.side_effect = [r1, r2]
        app = _mkapp(router)
        app.dependency_overrides[get_async_session] = _make_session(db)
        resp = TestClient(app).get("/civic/municipalities/gcc/wards")
        assert resp.status_code == 200
        data = resp.json()
        assert data["slug"] == "gcc"
        assert data["ward_count"] == 200
        assert data["type"] == "FeatureCollection"
        assert data["features"] == []

    def test_wards_row_with_geojson_parsed(self):
        """Ward row with valid geojson string → parsed geometry in Feature."""
        from api.v1.civic_intel import router

        m = MagicMock()
        m.short_name = "GCC"
        m.ward_count = 200
        ward = MagicMock()
        ward.feature_id = "W1"
        ward.attributes_json = {"ward_name": "Ward 1", "ward_number": 1}
        ward.geojson = '{"type":"Polygon","coordinates":[]}'
        r1 = MagicMock()
        r1.scalar_one_or_none.return_value = m
        r2 = MagicMock()
        r2.all.return_value = [ward]
        db = _mock_db()
        db.execute.side_effect = [r1, r2]
        app = _mkapp(router)
        app.dependency_overrides[get_async_session] = _make_session(db)
        resp = TestClient(app).get("/civic/municipalities/gcc/wards")
        assert resp.status_code == 200
        features = resp.json()["features"]
        assert len(features) == 1
        f = features[0]
        assert f["type"] == "Feature"
        assert f["geometry"]["type"] == "Polygon"
        assert f["properties"]["ward_name"] == "Ward 1"
        assert f["properties"]["feature_id"] == "W1"

    def test_wards_row_geojson_none_returns_null_geometry(self):
        """Ward row with geojson=None → geometry: null."""
        from api.v1.civic_intel import router

        m = MagicMock()
        m.short_name = "VMC"
        m.ward_count = 50
        ward = MagicMock()
        ward.feature_id = "W2"
        ward.attributes_json = {"ward_name": "Ward 2"}
        ward.geojson = None
        r1 = MagicMock()
        r1.scalar_one_or_none.return_value = m
        r2 = MagicMock()
        r2.all.return_value = [ward]
        db = _mock_db()
        db.execute.side_effect = [r1, r2]
        app = _mkapp(router)
        app.dependency_overrides[get_async_session] = _make_session(db)
        resp = TestClient(app).get("/civic/municipalities/vmc/wards")
        assert resp.status_code == 200
        features = resp.json()["features"]
        assert len(features) == 1
        assert features[0]["geometry"] is None
        assert features[0]["properties"]["ward_name"] == "Ward 2"


# ══════════════════════════════════════════════════════════════════════════════
# ADMIN — TRIGGER INGEST
# ══════════════════════════════════════════════════════════════════════════════


class TestTriggerIngest:
    def _admin_app(self):
        from api.v1.civic_intel import router

        app = _mkapp(router)
        app.dependency_overrides[get_current_user] = lambda: _admin_user()
        app.dependency_overrides[require_role(Role.OPERATOR)] = lambda: _admin_user()
        return app

    def test_no_scheduler_returns_503(self):
        """503 when etl_scheduler is not initialised on app.state."""
        app = self._admin_app()
        # intentionally no etl_scheduler set
        resp = TestClient(app).post("/admin/civic/ingest/lgd")
        assert resp.status_code == 503
        assert "not initialized" in resp.json()["detail"]

    def test_invalid_pipeline_name_returns_400(self):
        """400 for a pipeline name not in valid_pipelines list."""
        app = self._admin_app()
        mock_scheduler = MagicMock()
        app.state.etl_scheduler = mock_scheduler
        resp = TestClient(app).post("/admin/civic/ingest/nonexistent")
        assert resp.status_code == 400
        assert "Invalid pipeline" in resp.json()["detail"]

    def test_pipeline_result_none_returns_failed_status(self):
        """run_pipeline returning None → response status=failed."""
        app = self._admin_app()
        mock_scheduler = MagicMock()
        mock_scheduler.run_pipeline = AsyncMock(return_value=None)
        app.state.etl_scheduler = mock_scheduler
        resp = TestClient(app).post("/admin/civic/ingest/lgd")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "failed"
        assert data["pipeline"] == "lgd"
        assert "Pipeline execution failed" in data["error"]

    def test_pipeline_result_with_data_returns_all_fields(self):
        """Successful run; all result fields mapped to response."""
        app = self._admin_app()
        result = MagicMock()
        result.status = "success"
        result.records_fetched = 1000
        result.records_inserted = 800
        result.records_updated = 150
        result.records_skipped = 50
        result.error_message = None
        mock_scheduler = MagicMock()
        mock_scheduler.run_pipeline = AsyncMock(return_value=result)
        app.state.etl_scheduler = mock_scheduler
        resp = TestClient(app).post("/admin/civic/ingest/lgd")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert data["records_fetched"] == 1000
        assert data["records_inserted"] == 800
        assert data["records_updated"] == 150
        assert data["records_skipped"] == 50
        assert data["error"] is None

    @pytest.mark.parametrize(
        "pipeline",
        [
            "lgd",
            "boundaries",
            "osm_civic",
            "datagov",
            "municipal",
            "grievance",
        ],
    )
    def test_all_six_valid_pipelines_accepted(self, pipeline):
        """All 6 valid pipeline names reach run_pipeline without 400."""
        app = self._admin_app()
        result = MagicMock()
        result.status = "success"
        result.records_fetched = 0
        result.records_inserted = 0
        result.records_updated = 0
        result.records_skipped = 0
        result.error_message = None
        mock_scheduler = MagicMock()
        mock_scheduler.run_pipeline = AsyncMock(return_value=result)
        app.state.etl_scheduler = mock_scheduler
        resp = TestClient(app).post(f"/admin/civic/ingest/{pipeline}")
        assert resp.status_code == 200
        assert resp.json()["pipeline"] == pipeline


# ══════════════════════════════════════════════════════════════════════════════
# ADMIN — ETL LOG
# ══════════════════════════════════════════════════════════════════════════════


class TestGetETLLog:
    def _app(self, logs):
        from api.v1.civic_intel import router

        db = _mock_db()
        db.execute.return_value.scalars.return_value.all.return_value = logs
        app = _mkapp(router)
        app.dependency_overrides[get_async_session] = _make_session(db)
        return app

    def _make_log(
        self,
        pipeline="lgd",
        status="success",
        finished_at=datetime(2024, 1, 1, 0, 5, tzinfo=timezone.utc),
    ):
        log = MagicMock()
        log.id = 1
        log.pipeline_name = pipeline
        log.started_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
        log.finished_at = finished_at
        log.status = status
        log.records_fetched = 500
        log.records_inserted = 490
        log.records_updated = 10
        log.records_skipped = 0
        log.error_message = None
        return log

    def test_etl_log_no_filter_returns_logs(self):
        """All ETL logs returned when no pipeline filter."""
        app = self._app([self._make_log()])
        resp = TestClient(app).get("/admin/civic/etl-log")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["logs"]) == 1
        entry = data["logs"][0]
        assert entry["pipeline"] == "lgd"
        assert entry["status"] == "success"
        assert "2024-01-01" in entry["started_at"]
        assert entry["error"] is None

    def test_etl_log_with_pipeline_filter_empty(self):
        """Pipeline filter returns matching empty set."""
        app = self._app([])
        resp = TestClient(app).get("/admin/civic/etl-log", params={"pipeline": "boundaries"})
        assert resp.status_code == 200
        assert resp.json()["logs"] == []

    def test_etl_log_finished_at_none_serialized_as_null(self):
        """finished_at=None → null in JSON; status=running."""
        app = self._app([self._make_log(pipeline="osm_civic", status="running", finished_at=None)])
        resp = TestClient(app).get("/admin/civic/etl-log")
        assert resp.status_code == 200
        entry = resp.json()["logs"][0]
        assert entry["finished_at"] is None
        assert entry["status"] == "running"


# ══════════════════════════════════════════════════════════════════════════════
# ADMIN — EXPORT
# ══════════════════════════════════════════════════════════════════════════════


class TestExportCivicData:
    def test_export_success_calls_exporter(self):
        """POST /admin/civic/export invokes CivicDataExporter and returns manifest."""
        from api.v1.civic_intel import router

        db = _mock_db()
        app = _mkapp(router)
        app.dependency_overrides[get_async_session] = _make_session(db)
        app.dependency_overrides[get_current_user] = lambda: _admin_user()
        app.dependency_overrides[require_role(Role.OPERATOR)] = lambda: _admin_user()
        manifest_data = {"files": ["lgd.json", "boundaries.geojson"], "total": 2}
        with patch("services.civic_intel.data_exporter.CivicDataExporter") as MockExp:
            mock_exp_instance = MagicMock()
            mock_exp_instance.export_all = AsyncMock(return_value=manifest_data)
            mock_exp_instance.export_dir = "/data/civic_intel"
            MockExp.return_value = mock_exp_instance
            resp = TestClient(app).post("/admin/civic/export")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert data["manifest"] == manifest_data
        assert data["export_dir"] == "/data/civic_intel"


# ══════════════════════════════════════════════════════════════════════════════
# COMPLAINT CLUSTERING
# ══════════════════════════════════════════════════════════════════════════════


class TestComplaintClusters:
    def test_clusters_empty_result(self):
        """find_clusters returning empty list → total_clusters=0."""
        from api.v1.civic_intel import router

        db = _mock_db()
        app = _mkapp(router)
        app.dependency_overrides[get_async_session] = _make_session(db)
        with patch("services.complaint_cluster.ComplaintClusterService") as mock_svc:
            mock_svc.find_clusters = AsyncMock(return_value=[])
            resp = TestClient(app).get("/civic/clusters")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_clusters"] == 0
        assert data["clusters"] == []

    def test_clusters_with_data_maps_fields(self):
        """Cluster object fields mapped correctly to response keys."""
        from api.v1.civic_intel import router

        db = _mock_db()
        app = _mkapp(router)
        app.dependency_overrides[get_async_session] = _make_session(db)
        cluster = MagicMock()
        cluster.cluster_id = 7
        cluster.centroid_lat = 13.08
        cluster.centroid_lon = 80.27
        cluster.point_count = 15
        cluster.radius_meters = 180.0
        cluster.dominant_issue_type = "pothole"
        cluster.avg_severity = 3.5
        cluster.issue_types = ["pothole", "road_damage"]
        with patch("services.complaint_cluster.ComplaintClusterService") as mock_svc:
            mock_svc.find_clusters = AsyncMock(return_value=[cluster])
            resp = TestClient(app).get("/civic/clusters", params={"city": "Chennai"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_clusters"] == 1
        c = data["clusters"][0]
        assert c["cluster_id"] == 7
        assert c["lat"] == 13.08
        assert c["complaint_count"] == 15
        assert c["dominant_type"] == "pothole"
        assert c["issue_types"] == ["pothole", "road_damage"]


# ══════════════════════════════════════════════════════════════════════════════
# HOTSPOTS
# ══════════════════════════════════════════════════════════════════════════════


class TestHotspots:
    def test_hotspots_returns_list(self):
        """get_hotspots returns hotspots list from service."""
        from api.v1.civic_intel import router

        db = _mock_db()
        app = _mkapp(router)
        app.dependency_overrides[get_async_session] = _make_session(db)
        expected = [{"lat": 13.08, "lon": 80.27, "count": 30, "severity": 4}]
        with patch("services.complaint_cluster.ComplaintClusterService") as mock_svc:
            mock_svc.get_hotspots = AsyncMock(return_value=expected)
            resp = TestClient(app).get("/civic/hotspots", params={"city": "Chennai"})
        assert resp.status_code == 200
        assert resp.json()["hotspots"] == expected


# ══════════════════════════════════════════════════════════════════════════════
# ESCALATION RISK
# ══════════════════════════════════════════════════════════════════════════════


class TestEscalationRisk:
    def test_escalation_risk_empty(self):
        """No predictions above threshold → total_at_risk=0."""
        from api.v1.civic_intel import router

        db = _mock_db()
        app = _mkapp(router)
        app.dependency_overrides[get_async_session] = _make_session(db)
        with patch("services.escalation_predictor.EscalationPredictor") as mock_pred:
            mock_pred.batch_predict = AsyncMock(return_value=[])
            resp = TestClient(app).get("/civic/escalation-risk")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_at_risk"] == 0
        assert data["predictions"] == []

    def test_escalation_risk_with_prediction_fields(self):
        """Prediction object fields mapped correctly."""
        from api.v1.civic_intel import router

        db = _mock_db()
        app = _mkapp(router)
        app.dependency_overrides[get_async_session] = _make_session(db)
        pred = MagicMock()
        pred.issue_uuid = "uuid-abcd"
        pred.risk_score = 0.87
        pred.risk_level = "HIGH"
        pred.contributing_factors = ["age_days", "no_updates", "repeat_location"]
        pred.recommended_action = "escalate_to_commissioner"
        pred.predicted_escalation_hours = 6.0
        with patch("services.escalation_predictor.EscalationPredictor") as mock_pred:
            mock_pred.batch_predict = AsyncMock(return_value=[pred])
            resp = TestClient(app).get("/civic/escalation-risk", params={"min_risk": 0.7})
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_at_risk"] == 1
        p = data["predictions"][0]
        assert p["issue_uuid"] == "uuid-abcd"
        assert p["risk_score"] == 0.87
        assert p["risk_level"] == "HIGH"
        assert p["recommended_action"] == "escalate_to_commissioner"
        assert p["predicted_escalation_hours"] == 6.0


# ══════════════════════════════════════════════════════════════════════════════
# STREETLIGHTS — QR LOOKUP
# ══════════════════════════════════════════════════════════════════════════════


class TestStreetlightQR:
    def test_qr_found_returns_pole_data(self):
        """QR lookup returns all pole fields; last_maintenance=None → null."""
        from api.v1.civic_intel import router

        db = _mock_db()
        app = _mkapp(router)
        app.dependency_overrides[get_async_session] = _make_session(db)
        pole = MagicMock()
        pole.pole_id = "POLE-001"
        pole.qr_code = "QR-ABC123"
        pole.city = "Chennai"
        pole.ward_id = "W-01"
        pole.street_name = "Anna Salai"
        pole.is_operational = True
        pole.lamp_type = "LED"
        pole.wattage = 60
        pole.failure_count = 2
        pole.last_maintenance = None
        pole.authority = "GCC"
        with patch("services.streetlight_service.StreetlightService") as mock_svc:
            mock_svc.lookup_by_qr = AsyncMock(return_value=pole)
            resp = TestClient(app).get("/civic/streetlights/qr/QR-ABC123")
        assert resp.status_code == 200
        data = resp.json()
        assert data["pole_id"] == "POLE-001"
        assert data["city"] == "Chennai"
        assert data["lamp_type"] == "LED"
        assert data["is_operational"] is True
        assert data["last_maintenance"] is None

    def test_qr_not_found_returns_404(self):
        """Unknown QR code → 404."""
        from api.v1.civic_intel import router

        db = _mock_db()
        app = _mkapp(router)
        app.dependency_overrides[get_async_session] = _make_session(db)
        with patch("services.streetlight_service.StreetlightService") as mock_svc:
            mock_svc.lookup_by_qr = AsyncMock(return_value=None)
            resp = TestClient(app).get("/civic/streetlights/qr/UNKNOWN-QR")
        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"].lower()


# ══════════════════════════════════════════════════════════════════════════════
# STREETLIGHTS — NEARBY
# ══════════════════════════════════════════════════════════════════════════════


class TestNearbyStreetlights:
    def test_nearby_streetlights_returns_poles(self):
        """Returns list of nearby poles with core fields."""
        from api.v1.civic_intel import router

        db = _mock_db()
        app = _mkapp(router)
        app.dependency_overrides[get_async_session] = _make_session(db)
        pole = MagicMock()
        pole.pole_id = "POLE-002"
        pole.qr_code = "QR-XYZ"
        pole.is_operational = False
        pole.lamp_type = "Sodium"
        pole.failure_count = 5
        with patch("services.streetlight_service.StreetlightService") as mock_svc:
            mock_svc.find_nearby = AsyncMock(return_value=[pole])
            resp = TestClient(app).get(
                "/civic/streetlights/nearby", params={"lat": 13.08, "lon": 80.27}
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        p = data["poles"][0]
        assert p["pole_id"] == "POLE-002"
        assert p["is_operational"] is False
        assert p["failure_count"] == 5


# ══════════════════════════════════════════════════════════════════════════════
# STREETLIGHTS — OUTAGE REPORT
# ══════════════════════════════════════════════════════════════════════════════


class TestReportStreetlightOutage:
    def test_outage_recorded_for_existing_pole(self):
        """report_outage returns pole → outage_recorded response."""
        from api.v1.civic_intel import router

        db = _mock_db()
        app = _mkapp(router)
        app.dependency_overrides[get_async_session] = _make_session(db)
        pole = MagicMock()
        pole.pole_id = "POLE-001"
        pole.failure_count = 3
        with patch("services.streetlight_service.StreetlightService") as mock_svc:
            mock_svc.report_outage = AsyncMock(return_value=pole)
            resp = TestClient(app).post("/civic/streetlights/POLE-001/outage")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "outage_recorded"
        assert data["pole_id"] == "POLE-001"
        assert data["failure_count"] == 3

    def test_outage_pole_not_found_returns_404(self):
        """report_outage returning None → 404."""
        from api.v1.civic_intel import router

        db = _mock_db()
        app = _mkapp(router)
        app.dependency_overrides[get_async_session] = _make_session(db)
        with patch("services.streetlight_service.StreetlightService") as mock_svc:
            mock_svc.report_outage = AsyncMock(return_value=None)
            resp = TestClient(app).post("/civic/streetlights/GHOST-POLE/outage")
        assert resp.status_code == 404


# ══════════════════════════════════════════════════════════════════════════════
# STREETLIGHTS — MAINTENANCE PREDICTION
# ══════════════════════════════════════════════════════════════════════════════


class TestStreetlightMaintenancePrediction:
    def test_maintenance_prediction_returns_list(self):
        """predict_maintenance result forwarded as predictions list."""
        from api.v1.civic_intel import router

        db = _mock_db()
        app = _mkapp(router)
        app.dependency_overrides[get_async_session] = _make_session(db)
        expected = [
            {"pole_id": "POLE-001", "priority_score": 0.95, "reason": "high_failure_count"},
            {"pole_id": "POLE-007", "priority_score": 0.78, "reason": "age"},
        ]
        with patch("services.streetlight_service.StreetlightService") as mock_svc:
            mock_svc.predict_maintenance = AsyncMock(return_value=expected)
            resp = TestClient(app).get(
                "/civic/streetlights/maintenance-prediction", params={"city": "Chennai", "top_n": 5}
            )
        assert resp.status_code == 200
        assert resp.json()["predictions"] == expected


# ══════════════════════════════════════════════════════════════════════════════
# OFFICER ROUTE OPTIMIZATION
# ══════════════════════════════════════════════════════════════════════════════


class TestOfficerRoute:
    def test_officer_route_with_stops(self):
        """Optimized route with one stop; all fields mapped."""
        from api.v1.civic_intel import router

        db = _mock_db()
        app = _mkapp(router)
        app.dependency_overrides[get_async_session] = _make_session(db)
        stop = MagicMock()
        stop.order = 1
        stop.complaint_ref = "C-001"
        stop.issue_type = "pothole"
        stop.severity = 4
        stop.lat = 13.08
        stop.lon = 80.27
        stop.distance_from_prev_km = 0.5
        stop.estimated_arrival_minutes = 5
        stop.ward_id = "W-01"
        route = MagicMock()
        route.officer_id = "OFF-001"
        route.total_stops = 1
        route.total_distance_km = 0.5
        route.estimated_duration_minutes = 15
        route.warnings = []
        route.stops = [stop]
        with patch("services.officer_route_optimizer.OfficerRouteOptimizer") as mock_opt:
            mock_opt.optimize_route = AsyncMock(return_value=route)
            resp = TestClient(app).get(
                "/civic/officer/route", params={"officer_id": "OFF-001", "lat": 13.08, "lon": 80.27}
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["officer_id"] == "OFF-001"
        assert data["total_stops"] == 1
        assert data["total_distance_km"] == 0.5
        assert data["warnings"] == []
        assert len(data["stops"]) == 1
        s = data["stops"][0]
        assert s["complaint_ref"] == "C-001"
        assert s["issue_type"] == "pothole"
        assert s["ward_id"] == "W-01"

    def test_officer_route_no_stops(self):
        """Officer with no nearby issues; empty stops and warning returned."""
        from api.v1.civic_intel import router

        db = _mock_db()
        app = _mkapp(router)
        app.dependency_overrides[get_async_session] = _make_session(db)
        route = MagicMock()
        route.officer_id = "OFF-002"
        route.total_stops = 0
        route.total_distance_km = 0.0
        route.estimated_duration_minutes = 0
        route.warnings = ["No open complaints in area"]
        route.stops = []
        with patch("services.officer_route_optimizer.OfficerRouteOptimizer") as mock_opt:
            mock_opt.optimize_route = AsyncMock(return_value=route)
            resp = TestClient(app).get(
                "/civic/officer/route",
                params={"officer_id": "OFF-002", "lat": 13.0, "lon": 80.0, "city": "Chennai"},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_stops"] == 0
        assert data["stops"] == []
        assert len(data["warnings"]) == 1
        assert "No open complaints" in data["warnings"][0]
