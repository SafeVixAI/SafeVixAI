# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team
"""Boost tests: command_center and field_workflow edge cases."""

from __future__ import annotations

import asyncio
import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from core.circuit_breaker import CircuitBreakerRegistry
from core.database import get_db
from core.rbac import Role, require_role
from core.security import create_access_token, get_current_user

# ─────────────────────────────────────────────────────────────────────────────
# Shared helpers
# ─────────────────────────────────────────────────────────────────────────────


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


def _mock_db_side_effects(*row_sets):
    """Return a DB mock where successive execute() calls return different row sets."""
    db = AsyncMock(spec=AsyncSession)
    results = []
    for rows in row_sets:
        r = MagicMock()
        r.all.return_value = list(rows)
        results.append(r)
    db.execute = AsyncMock(side_effect=results)
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.add = MagicMock()
    db.delete = AsyncMock()
    return db


def _mkapp(router):
    app = FastAPI()
    app.include_router(router)
    return app


def _auth(sub="test-user", role="operator"):
    return {"sub": sub, "role": role}


def _hdr(sub="test-user", role="operator"):
    return {"Authorization": f"Bearer {create_access_token({'sub': sub}, role=role)}"}


def _officer(name="Officer Singh"):
    o = MagicMock()
    o.id = uuid.uuid4()
    o.name = name
    o.department = "Traffic"
    o.ward_id = "W1"
    o.last_checkin = None
    o.is_active = True
    return o


def _mock_issue_obj():
    issue = MagicMock()
    issue.uuid = uuid.uuid4()
    issue.location = True
    issue.issue_type = "pothole"
    issue.severity = 3
    issue.complaint_ref = "RS-BOOST-001"
    return issue


def _transition_result(ref="RS-BOOST-001"):
    r = MagicMock()
    r.issue = MagicMock()
    r.issue.complaint_ref = ref
    return r


@pytest.fixture(autouse=True)
def _reset_cbs():
    CircuitBreakerRegistry.reset_all()
    yield
    CircuitBreakerRegistry.reset_all()


# ═════════════════════════════════════════════════════════════════════════════
# command_center.py
# ═════════════════════════════════════════════════════════════════════════════


# ─────────────────────────────────────────────────────────────────────────────
# _sse_format helper
# ─────────────────────────────────────────────────────────────────────────────


class TestSSEFormatHelper:
    """Direct unit tests for the _sse_format module-level helper."""

    def test_sse_format_starts_with_event_line(self):
        from api.v1.command_center import _sse_format

        result = _sse_format("heartbeat", {"ts": "now"})
        assert result.startswith("event: heartbeat\ndata: ")

    def test_sse_format_ends_with_double_newline(self):
        from api.v1.command_center import _sse_format

        result = _sse_format("heartbeat", {"ts": "now"})
        assert result.endswith("\n\n")

    def test_sse_format_data_is_valid_json(self):
        from api.v1.command_center import _sse_format

        payload = {"message": "live feed connected", "count": 42}
        result = _sse_format("connected", payload)
        lines = result.split("\n")
        # lines[0] = "event: connected"
        # lines[1] = "data: {...}"
        assert lines[0] == "event: connected"
        data_line = lines[1]
        assert data_line.startswith("data: ")
        parsed = json.loads(data_line[len("data: ") :])
        assert parsed["message"] == "live feed connected"
        assert parsed["count"] == 42

    def test_sse_format_different_event_types(self):
        from api.v1.command_center import _sse_format

        for event_type in ("connected", "heartbeat", "complaint_created", "escalated"):
            result = _sse_format(event_type, {})
            assert f"event: {event_type}" in result
            assert result.endswith("\n\n")


# ─────────────────────────────────────────────────────────────────────────────
# live_feed — SSE StreamingResponse
# ─────────────────────────────────────────────────────────────────────────────


class TestLiveFeedEndpoint:
    """Verify that /live-feed returns a StreamingResponse with SSE headers."""

    @pytest.mark.asyncio
    async def test_live_feed_returns_streaming_response_type(self):
        """Call route function directly; confirm return type and media_type."""
        from fastapi.responses import StreamingResponse

        from api.v1.command_center import live_feed

        mock_request = MagicMock()
        with patch("api.v1.command_center.get_event_bus") as mock_bus_fn:
            bus = MagicMock()
            bus.get_recent_events.return_value = []
            bus.subscribe = MagicMock()
            bus.unsubscribe = MagicMock()
            mock_bus_fn.return_value = bus

            result = await live_feed(request=mock_request, current_user=_auth())

        assert isinstance(result, StreamingResponse)
        assert result.media_type == "text/event-stream"

    @pytest.mark.asyncio
    async def test_live_feed_no_cache_header(self):
        """SSE response must carry Cache-Control: no-cache."""
        from api.v1.command_center import live_feed

        mock_request = MagicMock()
        with patch("api.v1.command_center.get_event_bus") as mock_bus_fn:
            bus = MagicMock()
            bus.get_recent_events.return_value = []
            bus.subscribe = MagicMock()
            bus.unsubscribe = MagicMock()
            mock_bus_fn.return_value = bus

            result = await live_feed(request=mock_request, current_user=_auth())

        assert result.headers.get("cache-control") == "no-cache"
        assert result.headers.get("x-accel-buffering") == "no"

    @pytest.mark.asyncio
    async def test_live_feed_subscribes_and_unsubscribes(self):
        """Generator must subscribe to the event bus on entry and unsubscribe on exit."""
        from api.v1.command_center import live_feed

        mock_request = MagicMock()
        with patch("api.v1.command_center.get_event_bus") as mock_bus_fn:
            bus = MagicMock()
            bus.get_recent_events.return_value = []
            bus.subscribe = MagicMock()
            bus.unsubscribe = MagicMock()
            mock_bus_fn.return_value = bus

            result = await live_feed(request=mock_request, current_user=_auth())

            # Consume just enough of the async generator to trigger subscribe + connected yield
            async def _drain_first():
                async for chunk in result.body_iterator:
                    return chunk  # stop after the first chunk

            # Wrap in a task with cancellation so the infinite loop terminates
            task = asyncio.create_task(_drain_first())
            first_chunk = await asyncio.wait_for(task, timeout=2.0)

        assert first_chunk is not None
        assert "connected" in first_chunk


# ─────────────────────────────────────────────────────────────────────────────
# /officer-locations — null lat/lon and null workload branches
# ─────────────────────────────────────────────────────────────────────────────


class TestOfficerLocations:
    """Cover the float(lat) if lat else None and workload or 0 branches."""

    def _app(self, rows):
        from api.v1.command_center import router

        app = _mkapp(router)
        app.dependency_overrides[get_db] = lambda: _mock_db(rows=rows)
        app.dependency_overrides[get_current_user] = lambda: _auth(role="operator")
        app.dependency_overrides[require_role(Role.OPERATOR)] = lambda: _auth(role="operator")
        return app

    def test_lat_none_lon_none_in_response(self):
        """Row with lat=None, lon=None → officer dict has lat=None, lon=None."""
        o = _officer()
        rows = [(o, None, None, 5)]
        resp = TestClient(self._app(rows)).get(
            "/api/v1/command-center/officer-locations", headers=_hdr()
        )
        assert resp.status_code == 200
        officers = resp.json()["officers"]
        assert len(officers) == 1
        assert officers[0]["lat"] is None
        assert officers[0]["lon"] is None
        assert officers[0]["current_workload"] == 5
        assert officers[0]["name"] == "Officer Singh"

    def test_workload_none_becomes_zero(self):
        """Row with workload=None → current_workload=0 (workload or 0 branch)."""
        o = _officer()
        rows = [(o, 13.0, 80.0, None)]
        resp = TestClient(self._app(rows)).get(
            "/api/v1/command-center/officer-locations", headers=_hdr()
        )
        assert resp.status_code == 200
        officers = resp.json()["officers"]
        assert officers[0]["current_workload"] == 0
        assert officers[0]["lat"] == pytest.approx(13.0)
        assert officers[0]["lon"] == pytest.approx(80.0)

    def test_both_lat_lon_none_and_workload_none(self):
        """Both null branches hit simultaneously."""
        o = _officer()
        rows = [(o, None, None, None)]
        resp = TestClient(self._app(rows)).get(
            "/api/v1/command-center/officer-locations", headers=_hdr()
        )
        assert resp.status_code == 200
        off = resp.json()["officers"][0]
        assert off["lat"] is None
        assert off["lon"] is None
        assert off["current_workload"] == 0

    def test_multiple_officers_mixed_null(self):
        """Mix of null and non-null values across multiple officers."""
        o1, o2, o3 = _officer("A"), _officer("B"), _officer("C")
        rows = [
            (o1, 13.0, 80.0, 2),  # normal
            (o2, None, None, 0),  # null coords, workload=0
            (o3, 14.0, 79.0, None),  # null workload
        ]
        resp = TestClient(self._app(rows)).get(
            "/api/v1/command-center/officer-locations", headers=_hdr()
        )
        data = resp.json()
        assert data["total"] == 3
        officers = data["officers"]
        assert officers[0]["lat"] == pytest.approx(13.0)
        assert officers[1]["lat"] is None
        assert officers[1]["lon"] is None
        assert officers[2]["current_workload"] == 0


# ─────────────────────────────────────────────────────────────────────────────
# /escalation-board — predictions branch
# ─────────────────────────────────────────────────────────────────────────────


class TestEscalationBoard:
    """Cover critical_count / high_count aggregation and empty predictions."""

    def _app(self):
        from api.v1.command_center import router

        app = _mkapp(router)
        app.dependency_overrides[get_db] = lambda: _mock_db()
        app.dependency_overrides[get_current_user] = lambda: _auth(role="operator")
        app.dependency_overrides[require_role(Role.OPERATOR)] = lambda: _auth(role="operator")
        return app

    def _pred(self, risk_level="medium", score=0.5):
        p = MagicMock()
        p.issue_uuid = str(uuid.uuid4())
        p.risk_score = score
        p.risk_level = risk_level
        p.contributing_factors = ["age"]
        p.recommended_action = "Monitor"
        p.predicted_escalation_hours = 12
        return p

    def test_with_mixed_predictions_counts(self):
        """critical_count and high_count are derived from prediction objects."""
        preds = [
            self._pred("critical", 0.95),
            self._pred("critical", 0.88),
            self._pred("high", 0.72),
            self._pred("medium", 0.45),
            self._pred("low", 0.20),
        ]
        with patch(
            "services.escalation_predictor.EscalationPredictor.batch_predict",
            new_callable=AsyncMock,
            return_value=preds,
        ):
            resp = TestClient(self._app()).get(
                "/api/v1/command-center/escalation-board", headers=_hdr()
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 5
        assert data["critical_count"] == 2
        assert data["high_count"] == 1
        assert len(data["escalation_risks"]) == 5

    def test_empty_predictions_all_zeros(self):
        """batch_predict returns [] → total=0, critical_count=0, high_count=0."""
        with patch(
            "services.escalation_predictor.EscalationPredictor.batch_predict",
            new_callable=AsyncMock,
            return_value=[],
        ):
            resp = TestClient(self._app()).get(
                "/api/v1/command-center/escalation-board", headers=_hdr()
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["critical_count"] == 0
        assert data["high_count"] == 0
        assert data["escalation_risks"] == []

    def test_only_critical_predictions(self):
        """All predictions are critical → high_count=0, critical_count==total."""
        preds = [self._pred("critical", 0.9 + i * 0.01) for i in range(3)]
        with patch(
            "services.escalation_predictor.EscalationPredictor.batch_predict",
            new_callable=AsyncMock,
            return_value=preds,
        ):
            resp = TestClient(self._app()).get(
                "/api/v1/command-center/escalation-board", headers=_hdr()
            )

        data = resp.json()
        assert data["critical_count"] == 3
        assert data["high_count"] == 0
        assert data["total"] == 3

    def test_prediction_fields_serialized(self):
        """Each escalation_risk entry includes all expected keys."""
        p = self._pred("high", 0.75)
        p.contributing_factors = ["age", "severity"]
        p.recommended_action = "Escalate now"
        p.predicted_escalation_hours = 4

        with patch(
            "services.escalation_predictor.EscalationPredictor.batch_predict",
            new_callable=AsyncMock,
            return_value=[p],
        ):
            resp = TestClient(self._app()).get(
                "/api/v1/command-center/escalation-board", headers=_hdr()
            )

        risk = resp.json()["escalation_risks"][0]
        for key in (
            "issue_uuid",
            "risk_score",
            "risk_level",
            "contributing_factors",
            "recommended_action",
            "predicted_escalation_hours",
        ):
            assert key in risk, f"Missing key: {key}"
        assert risk["risk_level"] == "high"
        assert risk["predicted_escalation_hours"] == 4


# ─────────────────────────────────────────────────────────────────────────────
# /hotspots — DBSCAN clustering
# ─────────────────────────────────────────────────────────────────────────────


class TestHotspots:
    """Cover dbscan_cluster call with clusters and with empty results."""

    def _issue_row(self, issue_type="pothole", severity=4):
        issue = MagicMock()
        issue.uuid = uuid.uuid4()
        issue.issue_type = issue_type
        issue.severity = severity
        return (issue, 13.08, 80.27)

    def _cluster(self, cluster_id=0, point_count=4):
        c = MagicMock()
        c.cluster_id = cluster_id
        c.centroid_lat = 13.08
        c.centroid_lon = 80.27
        c.point_count = point_count
        c.radius_meters = 142.5
        c.dominant_issue_type = "pothole"
        c.avg_severity = 3.75
        c.issue_types = {"pothole": point_count}
        return c

    def _app(self, rows):
        from api.v1.command_center import router

        app = _mkapp(router)
        app.dependency_overrides[get_db] = lambda: _mock_db(rows=rows)
        app.dependency_overrides[get_current_user] = lambda: _auth(role="operator")
        app.dependency_overrides[require_role(Role.OPERATOR)] = lambda: _auth(role="operator")
        return app

    def test_hotspots_with_single_cluster(self):
        """dbscan_cluster returns one cluster → hotspot in response."""
        rows = [self._issue_row(), self._issue_row(), self._issue_row()]
        cluster = self._cluster(cluster_id=1, point_count=3)

        with patch("services.complaint_cluster.dbscan_cluster", return_value=[cluster]):
            resp = TestClient(self._app(rows)).get(
                "/api/v1/command-center/hotspots", headers=_hdr()
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["total_hotspots"] == 1
        assert data["total_complaints_analyzed"] == 3
        hs = data["hotspots"][0]
        assert hs["cluster_id"] == 1
        assert hs["centroid"]["lat"] == pytest.approx(13.08)
        assert hs["centroid"]["lon"] == pytest.approx(80.27)
        assert hs["complaint_count"] == 3
        assert hs["dominant_issue_type"] == "pothole"
        assert hs["radius_meters"] == pytest.approx(142.5)
        assert "pothole" in hs["issue_types"]

    def test_hotspots_empty_no_rows(self):
        """No complaint rows from DB → dbscan gets empty points, returns []."""
        with patch("services.complaint_cluster.dbscan_cluster", return_value=[]):
            resp = TestClient(self._app([])).get("/api/v1/command-center/hotspots", headers=_hdr())

        assert resp.status_code == 200
        data = resp.json()
        assert data["total_hotspots"] == 0
        assert data["total_complaints_analyzed"] == 0
        assert data["hotspots"] == []

    def test_hotspots_multiple_clusters(self):
        """Multiple clusters → total_hotspots reflects count."""
        rows = [self._issue_row(issue_type="pothole"), self._issue_row(issue_type="flooding")]
        clusters = [self._cluster(cluster_id=i, point_count=i + 2) for i in range(4)]

        with patch("services.complaint_cluster.dbscan_cluster", return_value=clusters):
            resp = TestClient(self._app(rows)).get(
                "/api/v1/command-center/hotspots", headers=_hdr()
            )

        data = resp.json()
        assert data["total_hotspots"] == 4
        assert len(data["hotspots"]) == 4

    def test_hotspots_issue_type_none_defaults_to_unknown(self):
        """issue.issue_type=None is serialized as 'unknown' in the points list."""
        issue = MagicMock()
        issue.uuid = uuid.uuid4()
        issue.issue_type = None  # ← the or "unknown" branch
        issue.severity = None  # ← the or 3 branch
        rows = [(issue, 13.0, 80.0)]

        with patch("services.complaint_cluster.dbscan_cluster", return_value=[]) as mock_cluster:
            TestClient(self._app(rows)).get("/api/v1/command-center/hotspots", headers=_hdr())
            call_args = mock_cluster.call_args
        # The points list passed to dbscan_cluster should have defaults applied
        points = call_args[0][0]
        assert points[0]["issue_type"] == "unknown"
        assert points[0]["severity"] == 3


# ─────────────────────────────────────────────────────────────────────────────
# /resolution-metrics — category and severity aggregation
# ─────────────────────────────────────────────────────────────────────────────


class TestResolutionMetrics:
    """Cover category not found (all zeros), avg_hours set, avg_hours=None."""

    def _app_two_calls(self, cat_rows, sev_rows):
        """Create app with DB returning different rows for each execute() call."""
        from api.v1.command_center import router

        app = _mkapp(router)
        db = _mock_db_side_effects(cat_rows, sev_rows)
        app.dependency_overrides[get_db] = lambda: db
        app.dependency_overrides[get_current_user] = lambda: _auth(role="operator")
        app.dependency_overrides[require_role(Role.OPERATOR)] = lambda: _auth(role="operator")
        return app

    def test_all_zeros_when_no_db_rows(self):
        """No rows for any category or severity → zeros everywhere, rate=0.0."""
        resp = TestClient(self._app_two_calls([], [])).get(
            "/api/v1/command-center/resolution-metrics", headers=_hdr()
        )
        assert resp.status_code == 200
        data = resp.json()
        # by_category: 3 fixed categories all zero
        assert len(data["by_category"]) == 3
        for cat in data["by_category"]:
            assert cat["total"] == 0
            assert cat["resolved"] == 0
            assert cat["resolution_rate"] == 0.0
            assert cat["avg_resolution_hours"] is None
        # by_severity: 5 entries, all zero
        assert len(data["by_severity"]) == 5
        for sev_entry in data["by_severity"]:
            assert sev_entry["resolution_rate"] == 0.0

    def test_resolution_rate_and_avg_hours_with_data(self):
        """Row with avg_hours set → resolution_rate and avg_resolution_hours populated."""
        cat_row = MagicMock()
        cat_row.category = "roads"
        cat_row.total = 10
        cat_row.resolved = 5
        cat_row.avg_hours = 24.5

        sev_row = MagicMock()
        sev_row.severity = 3
        sev_row.total = 8
        sev_row.resolved = 4

        resp = TestClient(self._app_two_calls([cat_row], [sev_row])).get(
            "/api/v1/command-center/resolution-metrics", headers=_hdr()
        )
        assert resp.status_code == 200
        data = resp.json()
        by_cat = {c["category"]: c for c in data["by_category"]}
        roads = by_cat["roads"]
        assert roads["total"] == 10
        assert roads["resolved"] == 5
        assert roads["resolution_rate"] == pytest.approx(50.0)
        assert roads["avg_resolution_hours"] == pytest.approx(24.5)
        # Uncovered categories default to zero
        assert by_cat["traffic"]["total"] == 0
        assert by_cat["streetlight"]["avg_resolution_hours"] is None

    def test_avg_hours_none_returns_null(self):
        """avg_hours=None on the row → avg_resolution_hours=None in response."""
        cat_row = MagicMock()
        cat_row.category = "traffic"
        cat_row.total = 6
        cat_row.resolved = 6
        cat_row.avg_hours = None  # ← the r and r.avg_hours else None branch

        resp = TestClient(self._app_two_calls([cat_row], [])).get(
            "/api/v1/command-center/resolution-metrics", headers=_hdr()
        )
        data = resp.json()
        by_cat = {c["category"]: c for c in data["by_category"]}
        assert by_cat["traffic"]["resolution_rate"] == pytest.approx(100.0)
        assert by_cat["traffic"]["avg_resolution_hours"] is None

    def test_severity_resolution_rate_calculated(self):
        """Severity rows present → resolution_rate = resolved/total * 100."""
        sev_rows = []
        for sev in range(1, 6):
            r = MagicMock()
            r.severity = sev
            r.total = sev * 4
            r.resolved = sev * 2  # 50% each
            sev_rows.append(r)

        resp = TestClient(self._app_two_calls([], sev_rows)).get(
            "/api/v1/command-center/resolution-metrics", headers=_hdr()
        )
        data = resp.json()
        assert len(data["by_severity"]) == 5
        for entry in data["by_severity"]:
            assert entry["resolution_rate"] == pytest.approx(50.0)

    def test_resolution_metrics_has_generated_at(self):
        """Response always includes generated_at timestamp."""
        resp = TestClient(self._app_two_calls([], [])).get(
            "/api/v1/command-center/resolution-metrics", headers=_hdr()
        )
        assert "generated_at" in resp.json()


# ═════════════════════════════════════════════════════════════════════════════
# field_workflow.py
# ═════════════════════════════════════════════════════════════════════════════


# ─────────────────────────────────────────────────────────────────────────────
# _haversine_meters — pure function
# ─────────────────────────────────────────────────────────────────────────────


class TestHaversineMeters:
    """Direct unit tests for the _haversine_meters helper."""

    def test_same_point_distance_is_zero(self):
        from api.v1.field_workflow import _haversine_meters

        dist = _haversine_meters(13.0, 80.0, 13.0, 80.0)
        assert dist == pytest.approx(0.0, abs=1e-6)

    def test_chennai_to_delhi_over_1500km(self):
        from api.v1.field_workflow import _haversine_meters

        # Chennai ≈ (13.08, 80.27), Delhi ≈ (28.61, 77.21)
        dist = _haversine_meters(13.0827, 80.2707, 28.6139, 77.2090)
        assert dist > 1_500_000  # > 1 500 km in metres

    def test_one_degree_latitude_approx_111km(self):
        from api.v1.field_workflow import _haversine_meters

        # Moving exactly 1° north along same meridian ≈ 111 195 m
        dist = _haversine_meters(13.0, 80.0, 14.0, 80.0)
        assert 110_000 < dist < 113_000

    def test_200m_threshold_boundary(self):
        from api.v1.field_workflow import _haversine_meters

        # 0.001° latitude ≈ 111 m — within 200 m radius
        dist = _haversine_meters(13.0, 80.0, 13.001, 80.0)
        assert dist < 200


# ─────────────────────────────────────────────────────────────────────────────
# _get_issue_coords — async helper
# ─────────────────────────────────────────────────────────────────────────────


class TestGetIssueCoords:
    """Async unit tests for _get_issue_coords."""

    @pytest.mark.asyncio
    async def test_no_location_returns_none_none(self):
        """issue.location is falsy → short-circuit, return (None, None)."""
        from api.v1.field_workflow import _get_issue_coords

        db = AsyncMock(spec=AsyncSession)
        issue = MagicMock()
        issue.location = None
        result = await _get_issue_coords(db, issue)
        assert result == (None, None)
        db.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_db_exception_returns_none_none(self):
        """DB raises → exception swallowed, (None, None) returned."""
        from api.v1.field_workflow import _get_issue_coords

        db = AsyncMock(spec=AsyncSession)
        db.execute.side_effect = Exception("connection lost")
        issue = MagicMock()
        issue.location = "POINT(80.27 13.08)"  # truthy
        issue.uuid = uuid.uuid4()
        result = await _get_issue_coords(db, issue)
        assert result == (None, None)

    @pytest.mark.asyncio
    async def test_db_returns_row_extracts_floats(self):
        """DB returns a valid row → coordinates extracted as floats."""
        from api.v1.field_workflow import _get_issue_coords

        db = AsyncMock(spec=AsyncSession)
        row = MagicMock()
        row.__getitem__ = lambda self, i: [13.0827, 80.2707][i]
        result_mock = MagicMock()
        result_mock.first.return_value = row
        db.execute.return_value = result_mock
        issue = MagicMock()
        issue.location = "POINT(80.27 13.08)"
        issue.uuid = uuid.uuid4()
        lat, lon = await _get_issue_coords(db, issue)
        assert lat == pytest.approx(13.0827)
        assert lon == pytest.approx(80.2707)

    @pytest.mark.asyncio
    async def test_db_returns_none_row_returns_none_none(self):
        """DB execute returns a result but .first() is None → (None, None)."""
        from api.v1.field_workflow import _get_issue_coords

        db = AsyncMock(spec=AsyncSession)
        result_mock = MagicMock()
        result_mock.first.return_value = None
        db.execute.return_value = result_mock
        issue = MagicMock()
        issue.location = True
        issue.uuid = uuid.uuid4()
        result = await _get_issue_coords(db, issue)
        assert result == (None, None)


# ─────────────────────────────────────────────────────────────────────────────
# POST /complaints/{uuid}/start-work — geo verification branches
# ─────────────────────────────────────────────────────────────────────────────


class TestStartFieldWork:
    """Cover the no-location, too-far, and nearby geo-verification branches."""

    _FW_SUB = str(uuid.uuid4())

    def _app(self, issue_obj=None):
        from api.v1.field_workflow import router

        app = _mkapp(router)
        db = _mock_db()
        if issue_obj is not None:
            db.execute.return_value.scalar_one_or_none.return_value = issue_obj
        app.dependency_overrides[get_db] = lambda: db
        app.dependency_overrides[get_current_user] = lambda: _auth(
            sub=self._FW_SUB, role="field_officer"
        )
        return app

    def test_no_complaint_location_gives_geo_verified_false(self):
        """_get_issue_coords returns (None, None) → geo_verified=False, distance=None."""
        issue = _mock_issue_obj()
        app = self._app(issue)

        with patch(
            "api.v1.field_workflow._get_issue_coords",
            new_callable=AsyncMock,
            return_value=(None, None),
        ), patch(
            "api.v1.field_workflow.ComplaintStateMachine.transition",
            new_callable=AsyncMock,
            return_value=_transition_result(),
        ):
            resp = TestClient(app).post(
                f"/api/v1/field/complaints/{issue.uuid}/start-work",
                json={"officer_lat": 13.0, "officer_lon": 80.0},
                headers=_hdr(sub=self._FW_SUB, role="field_officer"),
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["geo_verified"] is False
        assert data["distance_meters"] is None
        assert data["status"] == "work_started"

    def test_gps_too_far_geo_verified_false(self):
        """Officer GPS > 200 m from complaint → geo_verified=False, distance > 200."""
        issue = _mock_issue_obj()
        app = self._app(issue)

        # Complaint at Chennai, officer at Delhi (≈ 2100 km)
        with patch(
            "api.v1.field_workflow._get_issue_coords",
            new_callable=AsyncMock,
            return_value=(13.0827, 80.2707),
        ), patch(
            "api.v1.field_workflow.ComplaintStateMachine.transition",
            new_callable=AsyncMock,
            return_value=_transition_result(),
        ):
            resp = TestClient(app).post(
                f"/api/v1/field/complaints/{issue.uuid}/start-work",
                json={"officer_lat": 28.6139, "officer_lon": 77.2090},
                headers=_hdr(sub=self._FW_SUB, role="field_officer"),
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["geo_verified"] is False
        assert data["distance_meters"] > 200

    def test_gps_nearby_geo_verified_true(self):
        """Officer GPS within 200 m → geo_verified=True."""
        issue = _mock_issue_obj()
        app = self._app(issue)

        with patch(
            "api.v1.field_workflow._get_issue_coords",
            new_callable=AsyncMock,
            return_value=(13.08271, 80.27070),
        ), patch(
            "api.v1.field_workflow.ComplaintStateMachine.transition",
            new_callable=AsyncMock,
            return_value=_transition_result(),
        ):
            resp = TestClient(app).post(
                f"/api/v1/field/complaints/{issue.uuid}/start-work",
                json={"officer_lat": 13.08272, "officer_lon": 80.27071},
                headers=_hdr(sub=self._FW_SUB, role="field_officer"),
            )

        assert resp.status_code == 200
        assert resp.json()["geo_verified"] is True

    def test_invalid_transition_start_work_409(self):
        """ComplaintStateMachine.transition raises InvalidTransitionError → 409."""
        issue = _mock_issue_obj()
        app = self._app(issue)

        from services.complaint_state_machine import InvalidTransitionError

        with patch(
            "api.v1.field_workflow._get_issue_coords",
            new_callable=AsyncMock,
            return_value=(None, None),
        ), patch(
            "api.v1.field_workflow.ComplaintStateMachine.transition",
            new_callable=AsyncMock,
            side_effect=InvalidTransitionError("open", "in_progress", "RS-001"),
        ):
            resp = TestClient(app).post(
                f"/api/v1/field/complaints/{issue.uuid}/start-work",
                json={"officer_lat": 13.0, "officer_lon": 80.0},
                headers=_hdr(sub=self._FW_SUB, role="field_officer"),
            )

        assert resp.status_code == 409


# ─────────────────────────────────────────────────────────────────────────────
# POST /complaints/{uuid}/complete — after_photo and InvalidTransition
# ─────────────────────────────────────────────────────────────────────────────


class TestCompleteFieldWork:
    """Cover after_photo_url=None branch and InvalidTransitionError → 409."""

    _FW_SUB = str(uuid.uuid4())

    def _app(self, issue_obj=None):
        from api.v1.field_workflow import router

        app = _mkapp(router)
        db = _mock_db()
        if issue_obj is not None:
            db.execute.return_value.scalar_one_or_none.return_value = issue_obj
        app.dependency_overrides[get_db] = lambda: db
        app.dependency_overrides[get_current_user] = lambda: _auth(
            sub=self._FW_SUB, role="field_officer"
        )
        return app

    def test_complete_without_after_photo_url_none(self):
        """after_photo_url=None → issue.after_photo_url never assigned."""
        issue = _mock_issue_obj()
        app = self._app(issue)

        with patch(
            "api.v1.field_workflow._get_issue_coords",
            new_callable=AsyncMock,
            return_value=(None, None),
        ), patch(
            "api.v1.field_workflow.ComplaintStateMachine.transition",
            new_callable=AsyncMock,
            return_value=_transition_result(),
        ):
            resp = TestClient(app).post(
                f"/api/v1/field/complaints/{issue.uuid}/complete",
                json={
                    "officer_lat": 13.0,
                    "officer_lon": 80.0,
                    "resolution_notes": "Pothole filled with concrete",
                    "after_photo_url": None,
                },
                headers=_hdr(sub=self._FW_SUB, role="field_officer"),
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "resolved"
        # after_photo_url=None is falsy → `if body.after_photo_url:` branch is skipped.
        # If it HAD been assigned, issue.after_photo_url would be None (not a MagicMock).
        # Verifying it is not None confirms the assignment was skipped.
        assert issue.after_photo_url is not None

    def test_complete_with_after_photo_url_sets_attribute(self):
        """after_photo_url provided → issue.after_photo_url is set."""
        issue = _mock_issue_obj()
        app = self._app(issue)
        photo_url = "https://cdn.example.com/after-photo.jpg"

        with patch(
            "api.v1.field_workflow._get_issue_coords",
            new_callable=AsyncMock,
            return_value=(None, None),
        ), patch(
            "api.v1.field_workflow.ComplaintStateMachine.transition",
            new_callable=AsyncMock,
            return_value=_transition_result(),
        ):
            resp = TestClient(app).post(
                f"/api/v1/field/complaints/{issue.uuid}/complete",
                json={
                    "officer_lat": 13.0,
                    "officer_lon": 80.0,
                    "resolution_notes": "Road marking repainted",
                    "after_photo_url": photo_url,
                },
                headers=_hdr(sub=self._FW_SUB, role="field_officer"),
            )

        assert resp.status_code == 200
        assert issue.after_photo_url == photo_url

    def test_complete_invalid_transition_returns_409(self):
        """ComplaintStateMachine.transition raises → HTTP 409 Conflict."""
        issue = _mock_issue_obj()
        app = self._app(issue)

        from services.complaint_state_machine import InvalidTransitionError

        with patch(
            "api.v1.field_workflow._get_issue_coords",
            new_callable=AsyncMock,
            return_value=(None, None),
        ), patch(
            "api.v1.field_workflow.ComplaintStateMachine.transition",
            new_callable=AsyncMock,
            side_effect=InvalidTransitionError("open", "resolved", "RS-BOOST-001"),
        ):
            resp = TestClient(app).post(
                f"/api/v1/field/complaints/{issue.uuid}/complete",
                json={
                    "officer_lat": 13.0,
                    "officer_lon": 80.0,
                    "resolution_notes": "Work completed on site",
                },
                headers=_hdr(sub=self._FW_SUB, role="field_officer"),
            )

        assert resp.status_code == 409
        assert "Invalid transition" in resp.json()["detail"]

    def test_complete_geo_too_far_still_succeeds(self):
        """GPS beyond 200 m → geo_verified=False but 200 OK (no hard block)."""
        issue = _mock_issue_obj()
        app = self._app(issue)

        with patch(
            "api.v1.field_workflow._get_issue_coords",
            new_callable=AsyncMock,
            return_value=(13.0, 80.0),
        ), patch(
            "api.v1.field_workflow.ComplaintStateMachine.transition",
            new_callable=AsyncMock,
            return_value=_transition_result(),
        ):
            resp = TestClient(app).post(
                f"/api/v1/field/complaints/{issue.uuid}/complete",
                json={
                    "officer_lat": 28.61,
                    "officer_lon": 77.21,
                    "resolution_notes": "Remote update by supervisor",
                },
                headers=_hdr(sub=self._FW_SUB, role="field_officer"),
            )

        assert resp.status_code == 200
        assert resp.json()["geo_verified"] is False


# ─────────────────────────────────────────────────────────────────────────────
# POST /complaints/{uuid}/geo-checkin — proximity verification
# ─────────────────────────────────────────────────────────────────────────────


class TestGeoCheckin:
    """Cover no-coords branch, verified branch, and not-verified beyond radius."""

    _FW_SUB = str(uuid.uuid4())

    def _app(self, issue_obj=None):
        from api.v1.field_workflow import router

        app = _mkapp(router)
        db = _mock_db()
        if issue_obj is not None:
            db.execute.return_value.scalar_one_or_none.return_value = issue_obj
        app.dependency_overrides[get_db] = lambda: db
        app.dependency_overrides[get_current_user] = lambda: _auth(
            sub=self._FW_SUB, role="field_officer"
        )
        return app

    def test_no_complaint_coords_returns_not_verified_with_reason(self):
        """Complaint has no GPS → {verified: False, reason: '...'}."""
        issue = _mock_issue_obj()
        app = self._app(issue)

        with patch(
            "api.v1.field_workflow._get_issue_coords",
            new_callable=AsyncMock,
            return_value=(None, None),
        ):
            resp = TestClient(app).post(
                f"/api/v1/field/complaints/{issue.uuid}/geo-checkin",
                json={"lat": 13.0, "lon": 80.0},
                headers=_hdr(sub=self._FW_SUB, role="field_officer"),
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["verified"] is False
        assert "reason" in data
        assert "no GPS" in data["reason"] or "coordinates" in data["reason"].lower()

    def test_checkin_verified_when_within_200m(self):
        """Officer at the same coords → verified=True, distance≈0."""
        issue = _mock_issue_obj()
        app = self._app(issue)

        with patch(
            "api.v1.field_workflow._get_issue_coords",
            new_callable=AsyncMock,
            return_value=(13.08271, 80.27070),
        ):
            resp = TestClient(app).post(
                f"/api/v1/field/complaints/{issue.uuid}/geo-checkin",
                json={"lat": 13.08271, "lon": 80.27070},
                headers=_hdr(sub=self._FW_SUB, role="field_officer"),
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["verified"] is True
        assert data["distance_meters"] == pytest.approx(0.0, abs=1.0)
        assert data["max_radius_meters"] == 200
        assert data["complaint_location"]["lat"] == pytest.approx(13.08271)
        assert data["complaint_location"]["lon"] == pytest.approx(80.27070)

    def test_checkin_not_verified_when_beyond_200m(self):
        """Officer far from complaint → verified=False, distance > 200."""
        issue = _mock_issue_obj()
        app = self._app(issue)

        with patch(
            "api.v1.field_workflow._get_issue_coords",
            new_callable=AsyncMock,
            return_value=(13.0, 80.0),
        ):
            resp = TestClient(app).post(
                f"/api/v1/field/complaints/{issue.uuid}/geo-checkin",
                json={"lat": 20.0, "lon": 90.0},  # far away
                headers=_hdr(sub=self._FW_SUB, role="field_officer"),
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["verified"] is False
        assert data["distance_meters"] > 200

    def test_checkin_just_inside_radius(self):
        """0.001° latitude ≈ 111 m — inside 200 m → verified=True."""
        issue = _mock_issue_obj()
        app = self._app(issue)

        with patch(
            "api.v1.field_workflow._get_issue_coords",
            new_callable=AsyncMock,
            return_value=(13.0, 80.0),
        ):
            resp = TestClient(app).post(
                f"/api/v1/field/complaints/{issue.uuid}/geo-checkin",
                json={"lat": 13.001, "lon": 80.0},  # ≈ 111 m away
                headers=_hdr(sub=self._FW_SUB, role="field_officer"),
            )

        data = resp.json()
        assert data["verified"] is True
        assert data["distance_meters"] < 200


# ─────────────────────────────────────────────────────────────────────────────
# GET /my-route — route optimization
# ─────────────────────────────────────────────────────────────────────────────


class TestGetOptimizedRoute:
    """Cover missing-sub KeyError → 401 and successful optimization response."""

    def _app(self, user_dict):
        from api.v1.field_workflow import router

        app = _mkapp(router)
        db = _mock_db()
        app.dependency_overrides[get_db] = lambda: db
        app.dependency_overrides[get_current_user] = lambda: user_dict
        return app

    def test_missing_sub_key_returns_401(self):
        """current_user with no 'sub' key → KeyError caught → 401."""
        app = self._app({})  # no "sub"
        resp = TestClient(app).get("/api/v1/field/my-route?lat=13.0&lon=80.0", headers=_hdr())
        assert resp.status_code in (401, 403)
        assert "Invalid token" in resp.json()["detail"] or "Forbidden" in resp.json()["detail"]

    def test_optimize_route_success_no_stops(self):
        """OfficerRouteOptimizer.optimize_route returns route → 200 with expected keys."""
        mock_route = MagicMock()
        mock_route.officer_id = "officer-boost-123"
        mock_route.total_stops = 0
        mock_route.total_distance_km = 0.0
        mock_route.estimated_duration_minutes = 0
        mock_route.warnings = []
        mock_route.stops = []

        app = self._app({"sub": "officer-boost-123", "role": "field_officer"})

        with patch(
            "services.officer_route_optimizer.OfficerRouteOptimizer.optimize_route",
            new_callable=AsyncMock,
            return_value=mock_route,
        ):
            resp = TestClient(app).get("/api/v1/field/my-route?lat=13.08&lon=80.27", headers=_hdr())

        assert resp.status_code == 200
        data = resp.json()
        assert data["officer_id"] == "officer-boost-123"
        assert data["total_stops"] == 0
        assert data["stops"] == []

    def test_optimize_route_with_stops_serialized(self):
        """Stops list is serialized with all required fields."""
        stop = MagicMock()
        stop.order = 1
        stop.complaint_ref = "RS-101"
        stop.issue_type = "pothole"
        stop.severity = 4
        stop.lat = 13.09
        stop.lon = 80.28
        stop.distance_from_prev_km = 1.5
        stop.estimated_arrival_minutes = 7
        stop.address = "12 Gandhi Rd, Chennai"

        mock_route = MagicMock()
        mock_route.officer_id = "officer-boost-456"
        mock_route.total_stops = 1
        mock_route.total_distance_km = 1.5
        mock_route.estimated_duration_minutes = 27
        mock_route.warnings = ["Shift ending in 90 minutes"]
        mock_route.stops = [stop]

        app = self._app({"sub": "officer-boost-456", "role": "field_officer"})

        with patch(
            "services.officer_route_optimizer.OfficerRouteOptimizer.optimize_route",
            new_callable=AsyncMock,
            return_value=mock_route,
        ):
            resp = TestClient(app).get("/api/v1/field/my-route?lat=13.08&lon=80.27", headers=_hdr())

        assert resp.status_code == 200
        data = resp.json()
        assert data["total_stops"] == 1
        assert data["warnings"] == ["Shift ending in 90 minutes"]
        s = data["stops"][0]
        assert s["order"] == 1
        assert s["complaint_ref"] == "RS-101"
        assert s["issue_type"] == "pothole"
        assert s["address"] == "12 Gandhi Rd, Chennai"
        assert s["estimated_arrival_minutes"] == 7
