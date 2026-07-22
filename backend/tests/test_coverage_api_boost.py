# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Coverage boost tests: command_center, analytics, authority, officers,
user, roadwatch, waze_feed, routing, challan, circuit_breaker_api, wards, tracking.
"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from core.circuit_breaker import CircuitBreakerRegistry
from core.database import get_db
from core.rbac import Role, require_role
from core.security import create_access_token, get_current_user, get_current_user_optional
from models.schemas import (
    AuthorityPreviewResponse,
    ChallanResponse,
    RoadInfrastructureResponse,
    RoadIssuesResponse,
    RoadReportResponse,
    RouteBounds,
    RoutePoint,
    RoutePreviewResponse,
)


def _auth(sub="test-user", role="operator"):
    return {"sub": sub, "role": role}


def _hdr(sub="test-user", role="operator"):
    return {"Authorization": f"Bearer {create_access_token({'sub': sub}, role=role)}"}


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


# ══════════════════════════════════════════════════════════════════════════════
# command_center
# ══════════════════════════════════════════════════════════════════════════════

class TestCommandCenter:

    @pytest.fixture(autouse=True)
    def _reset(self):
        CircuitBreakerRegistry.reset_all()

    def test_officer_locations_success(self):
        from api.v1.command_center import router
        app = _mkapp(router)
        app.dependency_overrides[get_db] = lambda: _mock_db(
            rows=[(MagicMock(), 13.0, 80.0, 0)])
        app.dependency_overrides[get_current_user] = lambda: _auth(role="operator")
        app.dependency_overrides[require_role(Role.OPERATOR)] = lambda: _auth(role="operator")
        from core.limiter import limiter
        app.dependency_overrides[limiter.limit] = lambda *a, **kw: lambda x: x
        resp = TestClient(app).get("/api/v1/command-center/officer-locations", headers=_hdr())
        assert resp.status_code == 200
        assert "officers" in resp.json()

    def test_officer_locations_401(self):
        from api.v1.command_center import router
        app = _mkapp(router)
        resp = TestClient(app).get("/api/v1/command-center/officer-locations")
        assert resp.status_code == 401

    def test_resolution_metrics_ok(self):
        from api.v1.command_center import router
        app = _mkapp(router)
        app.dependency_overrides[get_db] = lambda: _mock_db(rows=[])
        app.dependency_overrides[get_current_user] = lambda: _auth(role="operator")
        app.dependency_overrides[require_role(Role.OPERATOR)] = lambda: _auth(role="operator")
        from core.limiter import limiter
        app.dependency_overrides[limiter.limit] = lambda *a, **kw: lambda x: x
        resp = TestClient(app).get("/api/v1/command-center/resolution-metrics", headers=_hdr())
        assert resp.status_code == 200
        d = resp.json()
        assert "by_category" in d and len(d["by_category"]) == 3

    def test_event_bus_health_ok(self):
        from api.v1.command_center import router
        app = _mkapp(router)
        app.dependency_overrides[get_current_user] = lambda: _auth(role="operator")
        app.dependency_overrides[require_role(Role.OPERATOR)] = lambda: _auth(role="operator")
        from core.limiter import limiter
        app.dependency_overrides[limiter.limit] = lambda *a, **kw: lambda x: x
        resp = TestClient(app).get("/api/v1/command-center/event-bus-health", headers=_hdr())
        assert resp.status_code == 200
        assert "metrics" in resp.json()

    def test_hotspots_401(self):
        from api.v1.command_center import router
        app = _mkapp(router)
        resp = TestClient(app).get("/api/v1/command-center/hotspots")
        assert resp.status_code == 401

    def test_escalation_board_401(self):
        from api.v1.command_center import router
        app = _mkapp(router)
        resp = TestClient(app).get("/api/v1/command-center/escalation-board")
        assert resp.status_code == 401

    def test_resolution_metrics_401(self):
        from api.v1.command_center import router
        app = _mkapp(router)
        resp = TestClient(app).get("/api/v1/command-center/resolution-metrics")
        assert resp.status_code == 401

    def test_event_bus_health_401(self):
        from api.v1.command_center import router
        app = _mkapp(router)
        resp = TestClient(app).get("/api/v1/command-center/event-bus-health")
        assert resp.status_code == 401


# ══════════════════════════════════════════════════════════════════════════════
# analytics
# ══════════════════════════════════════════════════════════════════════════════

class TestAnalytics:

    def test_heatmap(self):
        from api.v1.analytics import router
        app = _mkapp(router)
        app.dependency_overrides[get_db] = lambda: _mock_db(rows=[])
        from core.limiter import limiter
        app.dependency_overrides[limiter.limit] = lambda *a, **kw: lambda x: x
        resp = TestClient(app).get("/api/v1/analytics/heatmap")
        assert resp.status_code == 200
        assert resp.json()["type"] == "FeatureCollection"

    def test_heatmap_category(self):
        from api.v1.analytics import router
        app = _mkapp(router)
        app.dependency_overrides[get_db] = lambda: _mock_db(rows=[])
        from core.limiter import limiter
        app.dependency_overrides[limiter.limit] = lambda *a, **kw: lambda x: x
        resp = TestClient(app).get("/api/v1/analytics/heatmap?category=roads")
        assert resp.status_code == 200

    def test_ward_summary(self):
        from api.v1.analytics import router
        app = _mkapp(router)
        app.dependency_overrides[get_db] = lambda: _mock_db(rows=[])
        from core.limiter import limiter
        app.dependency_overrides[limiter.limit] = lambda *a, **kw: lambda x: x
        with patch("api.v1.analytics.WardService.ensure_seeded"):
            resp = TestClient(app).get("/api/v1/analytics/ward-summary")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_sla_breach(self):
        from api.v1.analytics import router
        app = _mkapp(router)
        app.dependency_overrides[get_db] = lambda: _mock_db(rows=[])
        from core.limiter import limiter
        app.dependency_overrides[limiter.limit] = lambda *a, **kw: lambda x: x
        resp = TestClient(app).get("/api/v1/analytics/sla-breach")
        assert resp.status_code == 200

    def test_category_breakdown(self):
        from api.v1.analytics import router
        db = _mock_db()
        db.execute.return_value.all.return_value = [("roads", 5), ("traffic", 3)]
        app = _mkapp(router)
        app.dependency_overrides[get_db] = lambda: db
        from core.limiter import limiter
        app.dependency_overrides[limiter.limit] = lambda *a, **kw: lambda x: x
        resp = TestClient(app).get("/api/v1/analytics/category-breakdown")
        assert resp.status_code == 200
        assert resp.json()["roads"] == 5

    def test_category_breakdown_empty(self):
        from api.v1.analytics import router
        db = _mock_db()
        db.execute.return_value.all.return_value = []
        app = _mkapp(router)
        app.dependency_overrides[get_db] = lambda: db
        from core.limiter import limiter
        app.dependency_overrides[limiter.limit] = lambda *a, **kw: lambda x: x
        resp = TestClient(app).get("/api/v1/analytics/category-breakdown")
        assert resp.status_code == 200
        for k in ("roads", "traffic", "streetlight"):
            assert resp.json()[k] == 0


# ══════════════════════════════════════════════════════════════════════════════
# authority
# ══════════════════════════════════════════════════════════════════════════════

class TestAuthority:

    def _app(self):
        from api.v1.authority import router
        app = _mkapp(router)
        app.dependency_overrides[get_current_user] = lambda: _auth(role="field_officer")
        app.dependency_overrides[require_role(Role.FIELD_OFFICER)] = lambda: _auth(role="field_officer")
        from core.limiter import limiter
        app.dependency_overrides[limiter.limit] = lambda *a, **kw: lambda x: x
        return app

    def test_accept_bad_uuid(self):
        r = TestClient(self._app()).post(
            "/api/v1/authority/complaints/not-uuid/accept",
            json={"notes": "x"}, headers=_hdr(role="field_officer"))
        assert r.status_code == 422

    def test_reject_no_reason(self):
        r = TestClient(self._app()).post(
            f"/api/v1/authority/complaints/{uuid.uuid4()}/reject",
            json={}, headers=_hdr(role="field_officer"))
        assert r.status_code == 422

    def test_reject_short_reason(self):
        r = TestClient(self._app()).post(
            f"/api/v1/authority/complaints/{uuid.uuid4()}/reject",
            json={"reason": "bad"}, headers=_hdr(role="field_officer"))
        assert r.status_code == 422

    def test_escalate_short_reason(self):
        r = TestClient(self._app()).post(
            f"/api/v1/authority/complaints/{uuid.uuid4()}/escalate",
            json={"reason": "bad"}, headers=_hdr(role="field_officer"))
        assert r.status_code == 422

    def test_accept_no_auth(self):
        from api.v1.authority import router
        r = TestClient(_mkapp(router)).post(
            f"/api/v1/authority/complaints/{uuid.uuid4()}/accept",
            json={"notes": "x"})
        assert r.status_code == 401

    def test_pending_no_auth(self):
        from api.v1.authority import router
        r = TestClient(_mkapp(router)).get("/api/v1/authority/pending")
        assert r.status_code == 401


# ══════════════════════════════════════════════════════════════════════════════
# officers
# ══════════════════════════════════════════════════════════════════════════════

class TestOfficers:

    def test_me_no_auth(self):
        from api.v1.officers import router
        r = TestClient(_mkapp(router)).get("/api/v1/officers/me")
        assert r.status_code == 401

    def test_checkin_no_auth(self):
        from api.v1.officers import router
        r = TestClient(_mkapp(router)).post("/api/v1/officers/checkin", json={"lat": 13, "lon": 80})
        assert r.status_code == 401

    def test_workload_no_auth(self):
        from api.v1.officers import router
        r = TestClient(_mkapp(router)).get("/api/v1/officers/me/workload")
        assert r.status_code == 401


# ══════════════════════════════════════════════════════════════════════════════
# user
# ══════════════════════════════════════════════════════════════════════════════

class TestUserRoutes:

    def _app(self):
        from api.v1.user import router
        app = _mkapp(router)
        app.dependency_overrides[get_current_user] = lambda: _auth()
        from core.limiter import limiter
        app.dependency_overrides[limiter.limit] = lambda *a, **kw: lambda x: x
        return app

    def test_create_missing_name(self):
        r = TestClient(self._app()).post("/api/v1/users/", json={"blood_group": "O+"}, headers=_hdr())
        assert r.status_code == 422

    def test_create_no_auth(self):
        from api.v1.user import router
        r = TestClient(_mkapp(router)).post("/api/v1/users/", json={"name": "U", "emergency_contacts": []})
        assert r.status_code == 401

    def test_get_bad_uuid(self):
        r = TestClient(self._app()).get("/api/v1/users/not-uuid", headers=_hdr())
        assert r.status_code == 422

    def test_update_bad_uuid(self):
        r = TestClient(self._app()).put("/api/v1/users/not-uuid", json={"name": "X"}, headers=_hdr())
        assert r.status_code == 422

    def test_export_bad_uuid(self):
        r = TestClient(self._app()).get("/api/v1/users/not-uuid/export", headers=_hdr())
        assert r.status_code == 422

    def test_delete_bad_uuid(self):
        r = TestClient(self._app()).delete("/api/v1/users/not-uuid", headers=_hdr())
        assert r.status_code == 422

    def test_delete_no_auth(self):
        from api.v1.user import router
        r = TestClient(_mkapp(router)).delete(f"/api/v1/users/{uuid.uuid4()}")
        assert r.status_code == 401

    def test_get_no_auth(self):
        from api.v1.user import router
        r = TestClient(_mkapp(router)).get(f"/api/v1/users/{uuid.uuid4()}")
        assert r.status_code == 401

    def test_invalid_blood_group(self):
        r = TestClient(self._app()).post(
            "/api/v1/users/", json={"name": "T", "blood_group": "BAD", "emergency_contacts": []}, headers=_hdr())
        assert r.status_code == 422


# ══════════════════════════════════════════════════════════════════════════════
# roadwatch
# ══════════════════════════════════════════════════════════════════════════════

class TestRoadwatch:

    def _app(self):
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
        app.dependency_overrides[get_current_user] = lambda: _auth(role="field_officer")
        app.dependency_overrides[require_role(Role.FIELD_OFFICER)] = lambda: _auth(role="field_officer")
        app.dependency_overrides[require_role(Role.OPERATOR)] = lambda: _auth(role="operator")
        from core.limiter import limiter
        app.dependency_overrides[limiter.limit] = lambda *a, **kw: lambda x: x
        return app

    def test_nearby_issues(self):
        r = TestClient(self._app()).get("/api/v1/roads/issues?lat=13.08&lon=80.27&radius=5000")
        assert r.status_code == 200 and r.json()["count"] == 0

    def test_nearby_missing_params(self):
        r = TestClient(self._app()).get("/api/v1/roads/issues")
        assert r.status_code == 422

    def test_nearby_bad_statuses(self):
        r = TestClient(self._app()).get("/api/v1/roads/issues?lat=13.08&lon=80.27&statuses=bad")
        assert r.status_code == 422

    def test_authority_ok(self):
        r = TestClient(self._app()).get("/api/v1/roads/authority?lat=13.08&lon=80.27")
        assert r.status_code == 200 and r.json()["authority_name"] == "NHAI"

    def test_authority_missing_coords(self):
        r = TestClient(self._app()).get("/api/v1/roads/authority")
        assert r.status_code == 422

    def test_infrastructure_ok(self):
        r = TestClient(self._app()).get("/api/v1/roads/infrastructure?lat=13.08&lon=80.27")
        assert r.status_code == 200

    def test_infrastructure_missing(self):
        r = TestClient(self._app()).get("/api/v1/roads/infrastructure")
        assert r.status_code == 422

    def test_submit_report(self):
        r = TestClient(self._app()).post(
            "/api/v1/roads/report",
            data={"lat": 13.08, "lon": 80.27, "issue_type": "pothole", "severity": 4})
        assert r.status_code == 200 and r.json()["authority_name"] == "NHAI"

    def test_submit_bad_severity(self):
        r = TestClient(self._app()).post(
            "/api/v1/roads/report",
            data={"lat": 13.08, "lon": 80.27, "issue_type": "p", "severity": 10})
        assert r.status_code == 422

    def test_submit_missing_type(self):
        r = TestClient(self._app()).post(
            "/api/v1/roads/report", data={"lat": 13.08, "lon": 80.27, "severity": 3})
        assert r.status_code == 422

    def test_issue_details_bad_uuid(self):
        r = TestClient(self._app()).get("/api/v1/roads/issues/not-uuid")
        assert r.status_code == 422

    def test_timeline_bad_uuid(self):
        r = TestClient(self._app()).get("/api/v1/roads/issues/not-uuid/timeline")
        assert r.status_code == 422

    def test_confirm_bad_uuid(self):
        r = TestClient(self._app()).post("/api/v1/roads/report/not-uuid/confirm")
        assert r.status_code == 422

    def test_resolve_bad_uuid(self):
        r = TestClient(self._app()).post(
            "/api/v1/roads/report/not-uuid/resolve", headers=_hdr(role="field_officer"))
        assert r.status_code == 422

    def test_resolve_no_auth(self):
        from api.v1.roadwatch import router
        app = _mkapp(router)
        svc = MagicMock()
        app.state.roadwatch_service = svc
        r = TestClient(app).post(f"/api/v1/roads/report/{uuid.uuid4()}/resolve")
        assert r.status_code == 401

    def test_verify_no_auth(self):
        from api.v1.roadwatch import router
        app = _mkapp(router)
        svc = MagicMock()
        app.state.roadwatch_service = svc
        r = TestClient(app).patch(f"/api/v1/roads/report/{uuid.uuid4()}/verify")
        assert r.status_code == 401


# ══════════════════════════════════════════════════════════════════════════════
# waze_feed
# ══════════════════════════════════════════════════════════════════════════════

class TestWazeFeed:

    def test_feed_empty(self):
        from api.v1.waze_feed import router
        db = _mock_db()
        db.execute.return_value.fetchall.return_value = []
        app = _mkapp(router)
        app.dependency_overrides[get_db] = lambda: db
        from core.limiter import limiter
        app.dependency_overrides[limiter.limit] = lambda *a, **kw: lambda x: x
        r = TestClient(app).get("/api/v1/feeds/waze")
        assert r.status_code == 200 and "incidents" in r.json()

    def test_feed_with_rows(self):
        from api.v1.waze_feed import router
        recent = datetime.now(UTC).isoformat()
        row = MagicMock()
        row._mapping = {
            "id": str(uuid.uuid4()),
            "issue_type": "pothole",
            "description": "Pothole",
            "lat": 13.08, "lon": 80.27,
            "road_name": "GST",
            "location_address": "Chennai",
            "created_at": recent,
            "status": "acknowledged",
            "severity": 3,
        }
        db = _mock_db()
        db.execute.return_value.fetchall.return_value = [row]
        app = _mkapp(router)
        app.dependency_overrides[get_db] = lambda: db
        from core.limiter import limiter
        app.dependency_overrides[limiter.limit] = lambda *a, **kw: lambda x: x
        with patch("api.v1.waze_feed.get_settings"):
            r = TestClient(app).get("/api/v1/feeds/waze")
        assert r.status_code == 200
        assert r.json()["count"] >= 1

    def test_cifs_type(self):
        from api.v1.waze_feed import _to_cifs_subtype, _to_cifs_type
        assert _to_cifs_type("pothole") == "HAZARD_ON_ROAD"
        assert _to_cifs_subtype("pothole") == "HAZARD_ON_ROAD_POT_HOLE"

    def test_cifs_unknown(self):
        from api.v1.waze_feed import _to_cifs_subtype, _to_cifs_type
        assert _to_cifs_type("x") == "HAZARD_ON_ROAD"
        assert _to_cifs_subtype("x") == "HAZARD_ON_ROAD_OBJECT"

    def test_ts_none(self):
        from api.v1.waze_feed import _format_timestamp
        assert "/" in _format_timestamp(None)

    def test_ts_valid(self):
        from api.v1.waze_feed import _format_timestamp
        assert "/" in _format_timestamp("2026-05-22T10:30:00Z")

    def test_ts_bad(self):
        from api.v1.waze_feed import _format_timestamp
        assert "/" in _format_timestamp("bad")

    def test_empty_feed(self):
        from api.v1.waze_feed import _empty_feed
        r = _empty_feed("No data")
        assert r["incidents"] == [] and r["count"] == 0 and r["note"] == "No data"


# ══════════════════════════════════════════════════════════════════════════════
# routing
# ══════════════════════════════════════════════════════════════════════════════

class TestRouting:

    def _app(self):
        from api.v1.routing import router
        app = _mkapp(router)
        svc = MagicMock()
        svc.preview_route = AsyncMock(return_value=RoutePreviewResponse(
            provider="osrm", profile="driving-car", distance_meters=4250, duration_seconds=540,
            path=[RoutePoint(lat=13.08, lon=80.27)],
            bounds=RouteBounds(south=13, west=80, north=13.1, east=80.3),
            origin=RoutePoint(lat=13.08, lon=80.27),
            destination=RoutePoint(lat=13.04, lon=80.22),
            routes=[], selected_route_id="r1"))
        app.state.routing_service = svc
        from core.limiter import limiter
        app.dependency_overrides[limiter.limit] = lambda *a, **kw: lambda x: x
        return app

    def test_preview_ok(self):
        r = TestClient(self._app()).get(
            "/api/v1/routing/preview?origin_lat=13.08&origin_lon=80.27"
            "&destination_lat=13.04&destination_lon=80.22")
        assert r.status_code == 200 and r.json()["provider"] == "osrm"

    def test_preview_missing(self):
        r = TestClient(self._app()).get("/api/v1/routing/preview")
        assert r.status_code == 422

    def test_preview_bad_lat(self):
        r = TestClient(self._app()).get(
            "/api/v1/routing/preview?origin_lat=200&origin_lon=80"
            "&destination_lat=13&destination_lon=80")
        assert r.status_code == 422

    def test_safe_route_ok(self):
        from api.v1.routing import router
        app = _mkapp(router)
        from core.limiter import limiter
        app.dependency_overrides[limiter.limit] = lambda *a, **kw: lambda x: x
        with patch("api.v1.routing.get_safe_route", return_value={"route": "safe"}):
            r = TestClient(app).get(
                "/api/v1/routing/safe-route?origin_lat=13.08&origin_lon=80.27"
                "&destination_lat=13.04&destination_lon=80.22&prefer_safety=true")
        assert r.status_code == 200 and r.json()["route"] == "safe"

    def test_safe_route_err(self):
        from api.v1.routing import router
        app = _mkapp(router)
        from core.limiter import limiter
        app.dependency_overrides[limiter.limit] = lambda *a, **kw: lambda x: x
        with patch("api.v1.routing.get_safe_route", side_effect=Exception("fail")):
            r = TestClient(app).get(
                "/api/v1/routing/safe-route?origin_lat=13.08&origin_lon=80.27"
                "&destination_lat=13.04&destination_lon=80.22")
        assert r.status_code == 503

    def test_safe_route_missing(self):
        from api.v1.routing import router
        r = TestClient(_mkapp(router)).get("/api/v1/routing/safe-route")
        assert r.status_code == 422


# ══════════════════════════════════════════════════════════════════════════════
# challan
# ══════════════════════════════════════════════════════════════════════════════

class TestChallanRoutes:

    def test_calc_ok(self):
        from api.v1.challan import get_challan_service, router
        app = _mkapp(router)
        f = MagicMock()
        f.calculate_with_db = AsyncMock(return_value=ChallanResponse(
            violation_code="185", vehicle_class="car", state_code="TN",
            base_fine=10000, amount_due=10000, section="S185", description="DD"))
        app.dependency_overrides[get_challan_service] = lambda: f
        from core.limiter import limiter
        app.dependency_overrides[limiter.limit] = lambda *a, **kw: lambda x: x
        r = TestClient(app).post("/api/v1/challan/calculate",
            json={"violation_code": "185", "vehicle_class": "car", "state_code": "TN", "is_repeat": False})
        assert r.status_code == 200 and r.json()["base_fine"] == 10000

    def test_calc_missing(self):
        from api.v1.challan import get_challan_service, router
        app = _mkapp(router)
        app.dependency_overrides[get_challan_service] = lambda: MagicMock()
        from core.limiter import limiter
        app.dependency_overrides[limiter.limit] = lambda *a, **kw: lambda x: x
        r = TestClient(app).post("/api/v1/challan/calculate", json={})
        assert r.status_code == 422

    def test_dispute(self):
        from api.v1.challan import router
        app = _mkapp(router)
        from core.limiter import limiter
        app.dependency_overrides[limiter.limit] = lambda *a, **kw: lambda x: x
        r = TestClient(app).post("/api/v1/challan/dispute",
            json={"challan_ref": "C1", "violation_code": "185", "fine_amount": 10000, "mitigating_factors": "E"})
        assert r.status_code == 200 and "dispute_ref" in r.json()

    def test_dispute_missing(self):
        from api.v1.challan import router
        app = _mkapp(router)
        from core.limiter import limiter
        app.dependency_overrides[limiter.limit] = lambda *a, **kw: lambda x: x
        r = TestClient(app).post("/api/v1/challan/dispute", json={})
        assert r.status_code == 422

    def test_predict(self):
        from api.v1.challan import router
        app = _mkapp(router)
        from core.limiter import limiter
        app.dependency_overrides[limiter.limit] = lambda *a, **kw: lambda x: x
        r = TestClient(app).post("/api/v1/challan/predict",
            json={"vehicle_number": "TN01AB1234", "state_code": "TN",
                  "telemetry": {"speeding_events": 5, "harsh_braking_events": 3,
                                "night_driving_minutes": 120, "total_km_driven": 500.0}})
        assert r.status_code == 200 and "predicted_violations_count" in r.json()

    def test_predict_missing(self):
        from api.v1.challan import router
        app = _mkapp(router)
        from core.limiter import limiter
        app.dependency_overrides[limiter.limit] = lambda *a, **kw: lambda x: x
        r = TestClient(app).post("/api/v1/challan/predict", json={})
        assert r.status_code == 422


# ══════════════════════════════════════════════════════════════════════════════
# circuit_breaker_api
# ══════════════════════════════════════════════════════════════════════════════

class TestCircuitBreakerAPI:

    @pytest.fixture(autouse=True)
    def _reset(self):
        CircuitBreakerRegistry.reset_all()
        CircuitBreakerRegistry.get("test_breaker")

    def _admin_app(self):
        from api.v1.circuit_breaker_api import router
        app = _mkapp(router)
        app.dependency_overrides[get_current_user] = lambda: _auth(role="admin")
        app.dependency_overrides[require_role(Role.ADMIN)] = lambda: _auth(role="admin")
        from core.limiter import limiter
        app.dependency_overrides[limiter.limit] = lambda *a, **kw: lambda x: x
        return app

    def _user_app(self):
        from api.v1.circuit_breaker_api import router
        app = _mkapp(router)
        app.dependency_overrides[get_current_user] = lambda: _auth(role="user")
        from core.limiter import limiter
        app.dependency_overrides[limiter.limit] = lambda *a, **kw: lambda x: x
        return app

    def test_list(self):
        r = TestClient(self._admin_app()).get("/api/v1/circuit-breaker/", headers=_hdr(role="admin"))
        assert r.status_code == 200 and "test_breaker" in r.json()["breakers"]

    def test_list_401(self):
        from api.v1.circuit_breaker_api import router
        r = TestClient(_mkapp(router)).get("/api/v1/circuit-breaker/")
        assert r.status_code == 401

    def test_get_found(self):
        r = TestClient(self._admin_app()).get("/api/v1/circuit-breaker/test_breaker", headers=_hdr(role="admin"))
        assert r.status_code == 200 and "breaker" in r.json()

    def test_get_not_found(self):
        r = TestClient(self._admin_app()).get("/api/v1/circuit-breaker/nonexistent", headers=_hdr(role="admin"))
        assert r.status_code == 404

    def test_get_no_admin(self):
        r = TestClient(self._user_app()).get("/api/v1/circuit-breaker/test_breaker", headers=_hdr(role="user"))
        assert r.status_code == 403

    def test_reset(self):
        r = TestClient(self._admin_app()).post("/api/v1/circuit-breaker/reset", headers=_hdr(role="admin"))
        assert r.status_code == 200 and r.json()["status"] == "ok"

    def test_trigger_found(self):
        r = TestClient(self._admin_app()).post("/api/v1/circuit-breaker/trigger/test_breaker", headers=_hdr(role="admin"))
        assert r.status_code == 200 and "opened" in r.json()["message"]

    def test_trigger_not_found(self):
        r = TestClient(self._admin_app()).post("/api/v1/circuit-breaker/trigger/nonexistent", headers=_hdr(role="admin"))
        assert r.status_code == 404

    def test_close_found(self):
        r = TestClient(self._admin_app()).post("/api/v1/circuit-breaker/close/test_breaker", headers=_hdr(role="admin"))
        assert r.status_code == 200 and "closed" in r.json()["message"]

    def test_close_not_found(self):
        r = TestClient(self._admin_app()).post("/api/v1/circuit-breaker/close/nonexistent", headers=_hdr(role="admin"))
        assert r.status_code == 404


# ══════════════════════════════════════════════════════════════════════════════
# wards
# ══════════════════════════════════════════════════════════════════════════════

class TestWards:

    def _app(self):
        from api.v1.wards import router
        app = _mkapp(router)
        from core.limiter import limiter
        app.dependency_overrides[limiter.limit] = lambda *a, **kw: lambda x: x
        return app

    def test_list_empty(self):
        with patch("api.v1.wards.WardService.list_all_wards", return_value=[]):
            r = TestClient(self._app()).get("/api/v1/wards")
        assert r.status_code == 200 and r.json() == []

    def test_list_data(self):
        w = MagicMock()
        w.ward_id = "w01"
        w.ward_name = "W1"
        w.zone_name = "Z"
        w.city = "Chennai"
        w.state_code = "TN"
        w.population = 50000
        w.area_sqkm = 10.5
        with patch("api.v1.wards.WardService.list_all_wards", return_value=[w]):
            r = TestClient(self._app()).get("/api/v1/wards")
        assert r.status_code == 200 and r.json()[0]["ward_id"] == "w01"

    def test_locate_found(self):
        w = MagicMock()
        w.ward_id = "w05"
        w.ward_name = "R"
        w.zone_name = "N"
        w.city = "Chennai"
        w.state_code = "TN"
        w.population = 30000
        w.area_sqkm = 5.0
        with patch("api.v1.wards.WardService.find_ward_by_coordinates", return_value=w):
            r = TestClient(self._app()).get("/api/v1/wards/locate?lat=13.08&lon=80.27")
        assert r.status_code == 200 and r.json()["ward_id"] == "w05"

    def test_locate_not_found(self):
        with patch("api.v1.wards.WardService.find_ward_by_coordinates", return_value=None):
            r = TestClient(self._app()).get("/api/v1/wards/locate?lat=13.08&lon=80.27")
        assert r.status_code == 404

    def test_locate_missing(self):
        r = TestClient(self._app()).get("/api/v1/wards/locate")
        assert r.status_code == 422

    def test_stats_ok(self):
        w = MagicMock()
        w.ward_id = "w01"
        db = _mock_db()
        db.execute.return_value.scalar_one_or_none.return_value = w
        app = self._app()
        app.dependency_overrides[get_db] = lambda: db
        with patch("api.v1.wards.WardService.get_ward_stats", return_value={
            "ward_id": "w01", "open_issues": 5, "resolved_issues": 10,
            "rejected_issues": 2, "total_issues": 17, "resolution_rate": 58.82}):
            r = TestClient(app).get("/api/v1/wards/w01/stats")
        assert r.status_code == 200 and r.json()["open_issues"] == 5

    def test_stats_not_found(self):
        db = _mock_db()
        db.execute.return_value.scalar_one_or_none.return_value = None
        app = self._app()
        app.dependency_overrides[get_db] = lambda: db
        r = TestClient(app).get("/api/v1/wards/nonexistent/stats")
        assert r.status_code == 404


# ══════════════════════════════════════════════════════════════════════════════
# tracking
# ══════════════════════════════════════════════════════════════════════════════

class TestTracking:

    def test_is_valid_location(self):
        from api.v1.tracking import _is_valid_location
        assert _is_valid_location(10.0, minimum=-90, maximum=90)
        assert not _is_valid_location(100.0, minimum=-90, maximum=90)
        assert _is_valid_location(None, minimum=-90, maximum=90)
        assert not _is_valid_location("bad", minimum=-90, maximum=90)

    def test_is_valid_payload(self):
        from api.v1.tracking import _is_valid_tracking_payload
        assert _is_valid_tracking_payload({"lat": 10.0, "lon": 20.0})
        assert _is_valid_tracking_payload({"latitude": 10.0, "longitude": 20.0})
        assert not _is_valid_tracking_payload({"lat": 100.0, "lon": 20.0})
        assert not _is_valid_tracking_payload("invalid")
        assert not _is_valid_tracking_payload({})
        assert not _is_valid_tracking_payload(None)

    def test_ws_token(self):
        from api.v1.tracking import _is_valid_ws_token
        t = create_access_token({"sub": "tu"})
        assert _is_valid_ws_token(t)
        assert not _is_valid_ws_token("bad")
        assert not _is_valid_ws_token(None)
        assert not _is_valid_ws_token("")

    def test_connection_health(self):
        from api.v1.tracking import ConnectionHealth
        ch = ConnectionHealth()
        w1, w2 = MagicMock(), MagicMock()
        ch.mark_activity(w1)
        ch.mark_activity(w2)
        ch.remove(w1)
        assert len(ch.stale_connections({w2}, timeout=99999)) == 0

    def test_redis_mgr(self):
        from api.v1.tracking import RedisConnectionManager
        m = RedisConnectionManager()
        assert m.redis is None
        m.set_redis(None)
        assert m.redis is None

    @pytest.mark.asyncio
    async def test_redis_broadcast(self):
        from api.v1.tracking import RedisConnectionManager
        await RedisConnectionManager().broadcast({"lat": 10.0}, "test")

    def test_ws_missing_token(self):
        from starlette.websockets import WebSocketDisconnect

        from api.v1.tracking import router
        app = FastAPI()
        app.include_router(router)
        with pytest.raises(WebSocketDisconnect) as exc, TestClient(app).websocket_connect(
            "/api/v1/tracking/group", headers={"origin": "http://localhost:3000"}):
            pass
        assert exc.value.code == 1008

    def test_ws_bad_json(self, monkeypatch):
        from api.v1.tracking import router
        monkeypatch.setattr("api.v1.tracking._origin_allowed", lambda x: True)
        app = FastAPI()
        app.include_router(router)
        with TestClient(app).websocket_connect(
            f"/api/v1/tracking/group?token={create_access_token({'sub':'tu'})}") as ws:
            ws.send_text("bad json")
            assert ws.receive_json()["type"] == "error"

    def test_ws_bad_payload(self, monkeypatch):
        from api.v1.tracking import router
        monkeypatch.setattr("api.v1.tracking._origin_allowed", lambda x: True)
        app = FastAPI()
        app.include_router(router)
        with TestClient(app).websocket_connect(
            f"/api/v1/tracking/group?token={create_access_token({'sub':'tu'})}") as ws:
            ws.send_json({"lat": 200, "lon": 20})
            assert ws.receive_json()["type"] == "error"

    def test_ws_valid(self, monkeypatch):
        from api.v1.tracking import router
        monkeypatch.setattr("api.v1.tracking._origin_allowed", lambda x: True)
        app = FastAPI()
        app.include_router(router)
        with TestClient(app).websocket_connect(
            f"/api/v1/tracking/group?token={create_access_token({'sub':'tu'})}") as ws:
            p = {"lat": 10, "lon": 20}
            ws.send_json(p)
            assert ws.receive_json() == p

    def test_ws_pong(self, monkeypatch):
        from api.v1.tracking import router
        monkeypatch.setattr("api.v1.tracking._origin_allowed", lambda x: True)
        app = FastAPI()
        app.include_router(router)
        with TestClient(app).websocket_connect(
            f"/api/v1/tracking/group?token={create_access_token({'sub':'tu'})}") as ws:
            ws.send_json({"type": "pong"})
            ws.send_json({"lat": 10, "lon": 20})
            assert ws.receive_json()["lat"] == 10
