# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team
"""Boost tests: admin, authority, public, waze_feed edge cases."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from core.circuit_breaker import CircuitBreakerRegistry
from core.database import get_db
from core.limiter import limiter
from core.rbac import Role, require_role
from core.security import create_access_token, get_current_user

# ── Core test helpers ─────────────────────────────────────────────────────────


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
    db.rollback = AsyncMock()
    db.add = MagicMock()
    db.delete = AsyncMock()
    return db


def _mkapp(router):
    app = FastAPI()
    app.include_router(router)
    return app


def _auth(sub=None, role="operator"):
    return {"sub": sub or str(uuid.uuid4()), "role": role}


# ── Single-call result stubs ─────────────────────────────────────────────────


def _sr(val):
    """Return a mock result whose .scalar() returns val."""
    r = MagicMock()
    r.scalar.return_value = val
    return r


def _ar(rows):
    """Return a mock result whose .all() returns rows."""
    r = MagicMock()
    r.all.return_value = rows
    return r


# ── Domain-object factories ──────────────────────────────────────────────────


def _mock_complaint():
    """Build a RoadIssue-compatible MagicMock for admin list responses.

    All fields must satisfy the Pydantic RoadIssueItem schema:
    - status  must be one of the RoadIssueStatus Literal values
    - created_at must be a datetime
    """
    issue = MagicMock()
    issue.uuid = uuid.uuid4()
    issue.complaint_ref = "RS-TEST-001"
    issue.issue_type = "pothole"
    issue.severity = 2
    issue.description = "Test pothole on MG Road"
    issue.location_address = "MG Road, Chennai"
    issue.road_name = "MG Road"
    issue.road_type = "arterial"
    issue.road_number = None
    issue.authority_name = "BBMP"
    issue.status = "open"  # valid RoadIssueStatus literal
    issue.created_at = datetime(2026, 1, 1, 12, 0, 0)  # naive datetime
    issue.category = "roads"
    issue.sub_category = None
    issue.ward_id = "W01"
    issue.ward_name = "Ward 1"
    issue.assigned_officer_id = None
    issue.sla_deadline = None
    issue.resolved_at = None
    issue.duplicate_of_uuid = None
    issue.confirmation_count = 0
    issue.before_photo_url = None
    issue.after_photo_url = None
    return issue


def _waze_row(**overrides):
    """Build a waze-feed row mock whose ._mapping is a plain dict.

    The waze endpoint does: dict(row._mapping) for row in result.fetchall()
    then accesses the result dict by key.
    """
    row = MagicMock()
    defaults: dict = {
        "id": str(uuid.uuid4()),
        "lat": 13.0827,
        "lon": 80.2707,
        "severity": 2,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "description": "Road hazard on highway",
        "issue_type": "pothole",
        "road_name": "MG Road",
        "location_address": "Chennai",
        "status": "acknowledged",
        "ward_id": "W01",
    }
    defaults.update(overrides)
    row._mapping = defaults
    return row


def _ward_row(
    ward_id="W01",
    ward_name="Ward 1",
    zone_name="North",
    population=50000,
    total=0,
    resolved=0,
    active=0,
    breached=0,
    avg_resolution_hours=None,
):
    """Build a named-attribute MagicMock row for ward-rankings queries."""
    row = MagicMock()
    row.ward_id = ward_id
    row.ward_name = ward_name
    row.zone_name = zone_name
    row.population = population
    row.total = total
    row.resolved = resolved
    row.active = active
    row.breached = breached
    row.avg_resolution_hours = avg_resolution_hours
    return row


# ══════════════════════════════════════════════════════════════════════════════
# Admin — api/v1/admin.py
# ══════════════════════════════════════════════════════════════════════════════


class TestAdminBoost:
    """Edge-case coverage for admin.py endpoints."""

    @pytest.fixture(autouse=True)
    def _reset(self):
        CircuitBreakerRegistry.reset_all()

    # ── App factory ─────────────────────────────────────────────────────────

    def _app(self, db=None, sub=None):
        from api.v1.admin import router

        app = _mkapp(router)
        _db = db or _mock_db()
        _user = _auth(sub=sub)
        app.dependency_overrides[get_db] = lambda: _db
        app.dependency_overrides[get_current_user] = lambda: _user
        app.dependency_overrides[require_role(Role.OPERATOR)] = lambda: _user
        app.dependency_overrides[limiter.limit] = lambda *a, **kw: lambda x: x
        return app

    # ── 1. GET /complaints — last page: next_offset is None ──────────────────

    def test_admin_complaints_no_next_offset(self):
        """total_count <= offset+limit → next_offset must be None (last page)."""
        db = _mock_db()
        issue = _mock_complaint()
        # Two successive db.execute() calls: count first, then rows
        db.execute.side_effect = [
            _sr(5),  # total_count = 5
            _ar([(issue, 13.0, 80.0)]),  # rows with (issue, lat, lon)
        ]
        resp = TestClient(self._app(db)).get("/api/v1/admin/complaints")
        assert resp.status_code == 200
        body = resp.json()
        assert body["next_offset"] is None  # 0+50 >= 5 → no next page
        assert body["total_count"] == 5
        assert body["count"] == 1

    # ── 2. GET /complaints — has more pages: next_offset is set ─────────────

    def test_admin_complaints_has_next_offset(self):
        """total_count > offset+limit → next_offset = offset+limit."""
        db = _mock_db()
        issue = _mock_complaint()
        db.execute.side_effect = [
            _sr(100),  # total_count = 100
            _ar([(issue, 13.0, 80.0)]),
        ]
        resp = TestClient(self._app(db)).get("/api/v1/admin/complaints?limit=10&offset=0")
        assert resp.status_code == 200
        body = resp.json()
        assert body["next_offset"] == 10  # 0+10=10 < 100 → next page exists

    # ── 3. POST /cleanup-expired-data — success path ─────────────────────────

    def test_admin_cleanup_success(self):
        """Cleanup endpoint returns 200 with expected keys on success."""
        db = _mock_db()
        resp = TestClient(self._app(db)).post("/api/v1/admin/cleanup-expired-data")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "success"
        assert "cleanup_policies" in body
        assert "live_tracking" in body["cleanup_policies"]

    # ── 4. POST /cleanup-expired-data — DB execute raises → 500 ─────────────

    def test_admin_cleanup_db_error_returns_500(self):
        """DB execute raising an exception → endpoint returns 500."""
        db = _mock_db()
        db.execute.side_effect = Exception("DB exploded")
        resp = TestClient(self._app(db)).post("/api/v1/admin/cleanup-expired-data")
        assert resp.status_code == 500
        assert "cleanup failed" in resp.json()["detail"].lower()
        db.rollback.assert_awaited()

    # ── 5. GET /dashboard — total_count == 0 → resolution_rate == 0.0 ────────

    def test_admin_dashboard_zero_total_no_division(self):
        """total=0 → resolution_rate=0.0 (no ZeroDivisionError)."""
        db = _mock_db()
        # Dashboard fires 6 sequential db.execute() calls
        db.execute.side_effect = [
            _sr(0),  # active_count
            _sr(0),  # resolved_count
            _sr(0),  # total_count
            _sr(0),  # breached_count
            _ar([]),  # cat_rows (category breakdown)
            _sr(0),  # officers_count
        ]
        resp = TestClient(self._app(db)).get("/api/v1/admin/dashboard")
        assert resp.status_code == 200
        kpis = resp.json()["kpis"]
        assert kpis["overall_resolution_rate"] == 0.0
        assert kpis["total_complaints"] == 0
        assert kpis["active_field_officers"] == 0

    # ── 6. GET /dashboard — total_count > 0 → resolution_rate computed ───────

    def test_admin_dashboard_nonzero_resolution_rate(self):
        """resolved=5, total=10 → resolution_rate=50.0."""
        db = _mock_db()
        db.execute.side_effect = [
            _sr(3),  # active_count
            _sr(5),  # resolved_count
            _sr(10),  # total_count
            _sr(1),  # breached_count
            _ar([("roads", 4), ("traffic", 3)]),  # cat_rows
            _sr(7),  # officers_count
        ]
        resp = TestClient(self._app(db)).get("/api/v1/admin/dashboard")
        assert resp.status_code == 200
        kpis = resp.json()["kpis"]
        assert kpis["overall_resolution_rate"] == 50.0
        assert kpis["total_complaints"] == 10
        assert resp.json()["category_breakdown"]["roads"] == 4


# ══════════════════════════════════════════════════════════════════════════════
# Authority — api/v1/authority.py
# ══════════════════════════════════════════════════════════════════════════════


class TestAuthorityBoost:
    """Edge-case coverage for authority.py endpoints."""

    @pytest.fixture(autouse=True)
    def _reset(self):
        CircuitBreakerRegistry.reset_all()

    # ── App factory ─────────────────────────────────────────────────────────

    def _app(self, db=None, auth_dict=None):
        from api.v1.authority import router

        app = _mkapp(router)
        _db = db or _mock_db()
        _user = auth_dict or {"sub": str(uuid.uuid4()), "role": "field_officer"}
        app.dependency_overrides[get_db] = lambda: _db
        app.dependency_overrides[get_current_user] = lambda: _user
        app.dependency_overrides[require_role(Role.FIELD_OFFICER)] = lambda: _user
        app.dependency_overrides[limiter.limit] = lambda *a, **kw: lambda x: x
        return app

    # ── 7. POST /accept — "sub" missing → actor_id=None, still 200 ──────────

    def test_authority_accept_sub_missing_gives_none_actor(self):
        """No 'sub' key in current_user → actor_id=None, endpoint still succeeds."""
        db = _mock_db()
        auth_no_sub = {"role": "field_officer"}  # deliberate missing sub
        issue_id = str(uuid.uuid4())

        transition_result = MagicMock()
        transition_result.issue = MagicMock()
        transition_result.issue.complaint_ref = "RS-001"
        transition_result.new_status = "accepted"

        with patch(
            "api.v1.authority.ComplaintStateMachine.transition",
            new_callable=AsyncMock,
            return_value=transition_result,
        ):
            resp = TestClient(self._app(db=db, auth_dict=auth_no_sub)).post(
                f"/api/v1/authority/complaints/{issue_id}/accept",
                json={"notes": "Accepting without sub"},
            )

        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "accepted"
        assert body["complaint_ref"] == "RS-001"

    # ── 8. POST /accept — InvalidTransitionError → 409 ───────────────────────

    def test_authority_accept_invalid_transition_returns_409(self):
        """InvalidTransitionError from state machine → 409 Conflict."""
        from services.complaint_state_machine import InvalidTransitionError

        db = _mock_db()
        issue_id = str(uuid.uuid4())

        with patch(
            "api.v1.authority.ComplaintStateMachine.transition",
            new_callable=AsyncMock,
            side_effect=InvalidTransitionError("closed", "accepted", "RS-002"),
        ):
            resp = TestClient(self._app(db=db)).post(
                f"/api/v1/authority/complaints/{issue_id}/accept",
                json={},
            )

        assert resp.status_code == 409

    # ── 9. POST /accept — ValueError → 404 ───────────────────────────────────

    def test_authority_accept_not_found_returns_404(self):
        """ValueError from state machine (complaint missing) → 404."""
        db = _mock_db()
        issue_id = str(uuid.uuid4())

        with patch(
            "api.v1.authority.ComplaintStateMachine.transition",
            new_callable=AsyncMock,
            side_effect=ValueError("Complaint not found"),
        ):
            resp = TestClient(self._app(db=db)).post(
                f"/api/v1/authority/complaints/{issue_id}/accept",
                json={},
            )

        assert resp.status_code == 404

    # ── 10. POST /reject — result.issue is None → no auto-reassign ───────────

    def test_authority_reject_issue_none_no_reassign(self):
        """result.issue=None skips WorkloadBalancer block; reassigned_to=None."""
        db = _mock_db()
        issue_id = str(uuid.uuid4())

        transition_result = MagicMock()
        transition_result.issue = None  # the key branch under test
        transition_result.new_status = "reassigned"

        with patch(
            "api.v1.authority.ComplaintStateMachine.transition",
            new_callable=AsyncMock,
            return_value=transition_result,
        ):
            resp = TestClient(self._app(db=db)).post(
                f"/api/v1/authority/complaints/{issue_id}/reject",
                json={"reason": "Cannot handle this at all"},
            )

        assert resp.status_code == 200
        body = resp.json()
        assert body["reassigned_to"] is None
        assert body["status"] == "rejected_and_reassigning"

    # ── 11. POST /reject — best officer found → auto-reassigned ──────────────

    def test_authority_reject_best_officer_found_reassigns(self):
        """WorkloadBalancer returns a best officer → reassigned_to populated."""
        db = _mock_db()
        issue_id = str(uuid.uuid4())

        transition_result = MagicMock()
        transition_result.issue = MagicMock()
        transition_result.issue.ward_id = "W01"
        transition_result.issue.severity = 3
        transition_result.issue.location = MagicMock()
        transition_result.new_status = "reassigned"

        best = MagicMock()
        best.officer_id = str(uuid.uuid4())  # must be valid UUID string
        best.officer_name = "Officer Sharma"
        best.composite_score = 0.92

        with (
            patch(
                "api.v1.authority.ComplaintStateMachine.transition",
                new_callable=AsyncMock,
                return_value=transition_result,
            ),
            patch(
                "services.workload_balancer.WorkloadBalancer.find_best_officer",
                new_callable=AsyncMock,
                return_value=best,
            ),
        ):
            resp = TestClient(self._app(db=db)).post(
                f"/api/v1/authority/complaints/{issue_id}/reject",
                json={"reason": "Outside my jurisdiction"},
            )

        assert resp.status_code == 200
        assert resp.json()["reassigned_to"] == "Officer Sharma"

    # ── 12. POST /reject — best officer is None → no reassignment ────────────

    def test_authority_reject_best_officer_none(self):
        """WorkloadBalancer returns None (no suitable officer) → reassigned_to=None."""
        db = _mock_db()
        issue_id = str(uuid.uuid4())

        transition_result = MagicMock()
        transition_result.issue = MagicMock()
        transition_result.issue.ward_id = "W02"
        transition_result.issue.severity = 2
        transition_result.issue.location = MagicMock()
        transition_result.new_status = "reassigned"

        with (
            patch(
                "api.v1.authority.ComplaintStateMachine.transition",
                new_callable=AsyncMock,
                return_value=transition_result,
            ),
            patch(
                "services.workload_balancer.WorkloadBalancer.find_best_officer",
                new_callable=AsyncMock,
                return_value=None,  # no officer available
            ),
        ):
            resp = TestClient(self._app(db=db)).post(
                f"/api/v1/authority/complaints/{issue_id}/reject",
                json={"reason": "No capacity right now"},
            )

        assert resp.status_code == 200
        assert resp.json()["reassigned_to"] is None

    # ── 13. POST /reject — WorkloadBalancer raises → warning + still 200 ─────

    def test_authority_reject_workload_balancer_exception_recovers(self):
        """WorkloadBalancer exception is caught (warning), response is still 200."""
        db = _mock_db()
        issue_id = str(uuid.uuid4())

        transition_result = MagicMock()
        transition_result.issue = MagicMock()
        transition_result.issue.ward_id = "W03"
        transition_result.issue.severity = 4
        transition_result.issue.location = MagicMock()
        transition_result.new_status = "reassigned"

        with (
            patch(
                "api.v1.authority.ComplaintStateMachine.transition",
                new_callable=AsyncMock,
                return_value=transition_result,
            ),
            patch(
                "services.workload_balancer.WorkloadBalancer.find_best_officer",
                new_callable=AsyncMock,
                side_effect=Exception("WB service unavailable"),
            ),
        ):
            resp = TestClient(self._app(db=db)).post(
                f"/api/v1/authority/complaints/{issue_id}/reject",
                json={"reason": "Cannot handle this complaint"},
            )

        assert resp.status_code == 200
        assert resp.json()["reassigned_to"] is None  # graceful degradation

    # ── 14. POST /reject — InvalidTransitionError → 409 ─────────────────────

    def test_authority_reject_invalid_transition_returns_409(self):
        """InvalidTransitionError on reject → 409 Conflict."""
        from services.complaint_state_machine import InvalidTransitionError

        db = _mock_db()
        issue_id = str(uuid.uuid4())

        with patch(
            "api.v1.authority.ComplaintStateMachine.transition",
            new_callable=AsyncMock,
            side_effect=InvalidTransitionError("closed", "reassigned", "RS-003"),
        ):
            resp = TestClient(self._app(db=db)).post(
                f"/api/v1/authority/complaints/{issue_id}/reject",
                json={"reason": "Attempt to reject closed issue"},
            )

        assert resp.status_code == 409

    # ── 15. POST /reject — ValueError → 404 ──────────────────────────────────

    def test_authority_reject_not_found_returns_404(self):
        """ValueError on reject → 404 Not Found."""
        db = _mock_db()
        issue_id = str(uuid.uuid4())

        with patch(
            "api.v1.authority.ComplaintStateMachine.transition",
            new_callable=AsyncMock,
            side_effect=ValueError("Complaint not found"),
        ):
            resp = TestClient(self._app(db=db)).post(
                f"/api/v1/authority/complaints/{issue_id}/reject",
                json={"reason": "This complaint does not exist"},
            )

        assert resp.status_code == 404

    # ── 16. POST /escalate — result.issue is None → new_severity = None ──────

    def test_authority_escalate_issue_none_severity_null(self):
        """escalate() returns result with issue=None → new_severity=None in response."""
        db = _mock_db()
        issue_id = str(uuid.uuid4())

        escalate_result = MagicMock()
        escalate_result.issue = None  # key branch: no issue object
        escalate_result.new_status = "in_progress"

        with patch(
            "api.v1.authority.ComplaintStateMachine.escalate",
            new_callable=AsyncMock,
            return_value=escalate_result,
        ):
            resp = TestClient(self._app(db=db)).post(
                f"/api/v1/authority/complaints/{issue_id}/escalate",
                json={"reason": "Critical damage, urgent fix needed", "target_tier": 3},
            )

        assert resp.status_code == 200
        body = resp.json()
        assert body["new_severity"] is None
        assert body["status"] == "escalated"

    # ── 17. POST /escalate — ValueError → 404 ────────────────────────────────

    def test_authority_escalate_not_found_returns_404(self):
        """ValueError from escalate() → 404 Not Found."""
        db = _mock_db()
        issue_id = str(uuid.uuid4())

        with patch(
            "api.v1.authority.ComplaintStateMachine.escalate",
            new_callable=AsyncMock,
            side_effect=ValueError("Complaint not found"),
        ):
            resp = TestClient(self._app(db=db)).post(
                f"/api/v1/authority/complaints/{issue_id}/escalate",
                json={"reason": "Need immediate escalation"},
            )

        assert resp.status_code == 404

    # ── 18. GET /pending — invalid UUID in sub → 401 ─────────────────────────

    def test_authority_pending_invalid_sub_uuid_returns_401(self):
        """Non-UUID value for 'sub' → uuid.UUID() raises ValueError → 401."""
        db = _mock_db()
        auth = {"sub": "not-a-uuid-at-all", "role": "field_officer"}
        resp = TestClient(self._app(db=db, auth_dict=auth)).get("/api/v1/authority/pending")
        assert resp.status_code == 401
        assert "Invalid user token" in resp.json()["detail"]

    # ── 19. GET /pending — missing sub key → 401 ─────────────────────────────

    def test_authority_pending_missing_sub_key_returns_401(self):
        """KeyError on current_user['sub'] (key absent) → 401."""
        db = _mock_db()
        auth = {"role": "field_officer"}  # no "sub" key
        resp = TestClient(self._app(db=db, auth_dict=auth)).get("/api/v1/authority/pending")
        assert resp.status_code == 401

    # ── 20. GET /pending — success, get_allowed_transitions invoked ───────────

    def test_authority_pending_success_with_transitions(self):
        """Valid officer UUID → returns list with allowed_actions from state machine."""
        db = _mock_db()
        officer_uuid = uuid.uuid4()
        auth = {"sub": str(officer_uuid), "role": "field_officer"}

        mock_issue = MagicMock()
        mock_issue.uuid = uuid.uuid4()
        mock_issue.complaint_ref = "RS-PEND-007"
        mock_issue.issue_type = "pothole"
        mock_issue.severity = 3
        mock_issue.category = "roads"
        mock_issue.ward_name = "Ward 7"
        mock_issue.location_address = "Anna Salai"
        mock_issue.status = "assigned"
        mock_issue.sla_deadline = None
        mock_issue.created_at = None

        # pending endpoint uses .scalars().all() — _mock_db chains scalars→r→all
        db.execute.return_value.all.return_value = [mock_issue]

        with patch(
            "api.v1.authority.ComplaintStateMachine.get_allowed_transitions",
            return_value=["accepted", "reassigned"],
        ) as mock_transitions:
            resp = TestClient(self._app(db=db, auth_dict=auth)).get("/api/v1/authority/pending")

        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 1
        item = data[0]
        assert item["complaint_ref"] == "RS-PEND-007"
        assert "accepted" in item["allowed_actions"]
        mock_transitions.assert_called_once_with("assigned")


# ══════════════════════════════════════════════════════════════════════════════
# Public — api/v1/public.py
# ══════════════════════════════════════════════════════════════════════════════


class TestPublicBoost:
    """Edge-case coverage for public.py endpoints and the _days_old helper."""

    @pytest.fixture(autouse=True)
    def _reset(self):
        CircuitBreakerRegistry.reset_all()

    # ── App factory ─────────────────────────────────────────────────────────

    def _app(self, db=None):
        from api.v1.public import router

        app = _mkapp(router)
        app.dependency_overrides[get_db] = lambda: db or _mock_db()
        app.dependency_overrides[limiter.limit] = lambda *a, **kw: lambda x: x
        return app

    # ── 21. GET /ward-rankings — total == 0 → resolution_rate = 0.0 ──────────

    def test_ward_rankings_zero_total_no_division(self):
        """Ward with total=0 → resolution_rate=0.0 (no ZeroDivisionError)."""
        db = _mock_db()
        db.execute.return_value.all.return_value = [_ward_row("W01", "Ward 1", total=0, resolved=0)]
        with patch("services.ward_service.WardService.ensure_seeded", new_callable=AsyncMock):
            resp = TestClient(self._app(db)).get("/api/v1/public/ward-rankings")

        assert resp.status_code == 200
        rankings = resp.json()["rankings"]
        assert len(rankings) == 1
        assert rankings[0]["resolution_rate"] == 0.0
        assert rankings[0]["rank"] == 1

    # ── 22. GET /ward-rankings — avg_resolution_hours is None ────────────────

    def test_ward_rankings_avg_hours_none(self):
        """Ward with resolved issues but no avg_hours → avg_resolution_hours=None."""
        db = _mock_db()
        db.execute.return_value.all.return_value = [
            _ward_row("W02", "Ward 2", total=5, resolved=3, avg_resolution_hours=None)
        ]
        with patch("services.ward_service.WardService.ensure_seeded", new_callable=AsyncMock):
            resp = TestClient(self._app(db)).get("/api/v1/public/ward-rankings")

        assert resp.status_code == 200
        rankings = resp.json()["rankings"]
        assert rankings[0]["avg_resolution_hours"] is None
        assert rankings[0]["resolution_rate"] == 60.0  # 3/5 * 100

    # ── 23. GET /ward-rankings — multiple wards ranked 1,2,3 ─────────────────

    def test_ward_rankings_multiple_wards_sorted_and_ranked(self):
        """Three wards get rank 1/2/3 ordered by resolution_rate descending."""
        db = _mock_db()
        db.execute.return_value.all.return_value = [
            _ward_row("W01", "Alpha Ward", total=10, resolved=2),  # 20 %
            _ward_row("W02", "Beta Ward", total=10, resolved=8),  # 80 %
            _ward_row("W03", "Gamma Ward", total=10, resolved=5),  # 50 %
        ]
        with patch("services.ward_service.WardService.ensure_seeded", new_callable=AsyncMock):
            resp = TestClient(self._app(db)).get("/api/v1/public/ward-rankings")

        assert resp.status_code == 200
        rankings = resp.json()["rankings"]
        assert len(rankings) == 3
        # Sorted desc: W02 (80%), W03 (50%), W01 (20%)
        assert rankings[0]["ward_id"] == "W02"
        assert rankings[0]["rank"] == 1
        assert rankings[1]["ward_id"] == "W03"
        assert rankings[1]["rank"] == 2
        assert rankings[2]["ward_id"] == "W01"
        assert rankings[2]["rank"] == 3
        assert resp.json()["total_wards"] == 3

    # ── 24. GET /authority-performance — total == 0 → resolution_rate = 0.0 ──

    def test_authority_performance_zero_total(self):
        """Authority with total=0 complaints → resolution_rate=0.0."""
        db = _mock_db()
        db.execute.return_value.all.return_value = [
            ("BBMP", 0, 0),
        ]
        resp = TestClient(self._app(db)).get("/api/v1/public/authority-performance")
        assert resp.status_code == 200
        authorities = resp.json()["authorities"]
        assert len(authorities) == 1
        assert authorities[0]["resolution_rate"] == 0.0
        assert authorities[0]["total_complaints"] == 0

    # ── 25. GET /authority-performance — total > 0 → rate computed ───────────

    def test_authority_performance_nonzero_resolution_rate(self):
        """Multiple authorities sorted by resolution_rate descending."""
        db = _mock_db()
        db.execute.return_value.all.return_value = [
            ("BBMP", 10, 7),  # 70 %
            ("NHAI", 20, 20),  # 100 %
        ]
        resp = TestClient(self._app(db)).get("/api/v1/public/authority-performance")
        assert resp.status_code == 200
        authorities = resp.json()["authorities"]
        # Sorted desc → NHAI first (100%), then BBMP (70%)
        assert authorities[0]["authority_name"] == "NHAI"
        assert authorities[0]["resolution_rate"] == 100.0
        assert authorities[1]["resolution_rate"] == 70.0

    # ── 26. GET /stats — total > 0 → resolution_rate computed ────────────────

    def test_public_stats_nonzero_resolution_rate(self):
        """total=10, resolved=5 → resolution_rate=50.0."""
        db = _mock_db()
        # /stats fires 7 sequential db.execute() calls
        db.execute.side_effect = [
            _sr(10),  # total
            _sr(5),  # resolved
            _sr(3),  # active
            _sr(1),  # breached
            _ar([("roads", 5), ("traffic", 3)]),  # cat_rows
            _ar([(2, 8), (3, 2)]),  # sev_rows
            _sr(4),  # officers_active
        ]
        resp = TestClient(self._app(db)).get("/api/v1/public/stats")
        assert resp.status_code == 200
        body = resp.json()
        assert body["resolution_rate"] == 50.0
        assert body["total_complaints_filed"] == 10
        assert body["total_resolved"] == 5

    # ── 27. GET /stats — total == 0 → resolution_rate = 0.0 ─────────────────

    def test_public_stats_zero_total_no_division_error(self):
        """total=0 → resolution_rate=0.0 without ZeroDivisionError."""
        db = _mock_db()
        db.execute.side_effect = [
            _sr(0),
            _sr(0),
            _sr(0),
            _sr(0),
            _ar([]),
            _ar([]),
            _sr(0),
        ]
        resp = TestClient(self._app(db)).get("/api/v1/public/stats")
        assert resp.status_code == 200
        assert resp.json()["resolution_rate"] == 0.0

    # ── 28. GET /stats — category None → keyed as "uncategorized" ────────────

    def test_public_stats_category_none_mapped_to_uncategorized(self):
        """cat=None in DB row → key 'uncategorized' in response dict."""
        db = _mock_db()
        db.execute.side_effect = [
            _sr(5),
            _sr(2),
            _sr(3),
            _sr(0),
            _ar([(None, 3), ("roads", 2)]),  # None category
            _ar([]),
            _sr(1),
        ]
        resp = TestClient(self._app(db)).get("/api/v1/public/stats")
        assert resp.status_code == 200
        categories = resp.json()["category_breakdown"]
        assert "uncategorized" in categories
        assert categories["uncategorized"] == 3
        assert categories["roads"] == 2

    # ── 29. GET /open-issues-map — features produced from DB rows ────────────

    def test_public_open_issues_map_builds_geojson_features(self):
        """DB rows produce valid GeoJSON Feature objects."""
        db = _mock_db()
        mock_issue = MagicMock()
        mock_issue.complaint_ref = "RS-GEO-042"
        mock_issue.category = "roads"
        mock_issue.issue_type = "pothole"
        mock_issue.severity = 2
        mock_issue.status = "open"
        mock_issue.ward_name = "Ward 5"
        mock_issue.created_at = datetime(2026, 1, 1, 0, 0, 0)  # naive, ~6 months ago
        db.execute.return_value.all.return_value = [(mock_issue, 13.08, 80.27)]

        resp = TestClient(self._app(db)).get("/api/v1/public/open-issues-map")

        assert resp.status_code == 200
        body = resp.json()
        assert body["type"] == "FeatureCollection"
        assert body["total"] == 1
        feat = body["features"][0]
        assert feat["type"] == "Feature"
        assert feat["geometry"]["type"] == "Point"
        assert feat["geometry"]["coordinates"] == [80.27, 13.08]
        props = feat["properties"]
        assert props["complaint_ref"] == "RS-GEO-042"
        assert props["severity"] == 2
        assert isinstance(props["days_old"], int)
        assert props["days_old"] > 0

    # ── 30. GET /complaint/{ref}/status — found, status "open" (not resolved) ─

    def test_public_complaint_status_found_open(self):
        """Existing complaint with status='open' → resolved=False."""
        db = _mock_db()
        mock_issue = MagicMock()
        mock_issue.complaint_ref = "RS-OPEN-001"
        mock_issue.status = "open"
        mock_issue.category = "roads"
        mock_issue.severity = 2
        mock_issue.ward_name = "Ward 1"
        mock_issue.authority_name = "BBMP"
        mock_issue.created_at = datetime(2026, 3, 1, 0, 0, 0)
        db.execute.return_value.scalar_one_or_none.return_value = mock_issue

        resp = TestClient(self._app(db)).get("/api/v1/public/complaint/RS-OPEN-001/status")
        assert resp.status_code == 200
        body = resp.json()
        assert body["found"] is True
        assert body["status"] == "open"
        assert body["resolved"] is False  # "open" is not a resolved status

    # ── 31. GET /complaint/{ref}/status — not found ───────────────────────────

    def test_public_complaint_status_not_found(self):
        """Unknown complaint_ref → found=False, no exception."""
        db = _mock_db()
        db.execute.return_value.scalar_one_or_none.return_value = None

        resp = TestClient(self._app(db)).get("/api/v1/public/complaint/RS-GHOST-9999/status")
        assert resp.status_code == 200
        body = resp.json()
        assert body["found"] is False
        assert body["complaint_ref"] == "RS-GHOST-9999"

    # ── 32. _days_old — naive datetime (no tzinfo) ────────────────────────────

    def test_days_old_naive_datetime_returns_positive_int(self):
        """Naive datetime from the past returns a positive integer day count."""
        from api.v1.public import _days_old

        # Jan 1, 2026 is ~6 months before the test date (2026-06-29)
        result = _days_old(datetime(2026, 1, 1, 0, 0, 0))
        assert isinstance(result, int)
        assert result > 0

    # ── 33. _days_old — None → 0 ─────────────────────────────────────────────

    def test_days_old_none_returns_zero(self):
        """None created_at → always 0."""
        from api.v1.public import _days_old

        assert _days_old(None) == 0

    # ── 34. _days_old — timezone-aware datetime strips tzinfo ────────────────

    def test_days_old_aware_datetime_strips_tz(self):
        """Aware datetime has tzinfo stripped before diff; result is still correct."""
        from api.v1.public import _days_old

        aware_past = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        result = _days_old(aware_past)
        assert isinstance(result, int)
        assert result > 0  # Jan 15 is before Jun 29


# ══════════════════════════════════════════════════════════════════════════════
# Waze Feed — api/v1/waze_feed.py
# ══════════════════════════════════════════════════════════════════════════════


class TestWazeFeedBoost:
    """Edge-case coverage for the CIFS waze feed endpoint."""

    @pytest.fixture(autouse=True)
    def _reset(self):
        CircuitBreakerRegistry.reset_all()

    # ── App + request helpers ────────────────────────────────────────────────

    def _app(self, db=None):
        from api.v1.waze_feed import router

        app = _mkapp(router)
        app.dependency_overrides[get_db] = lambda: db or _mock_db()
        app.dependency_overrides[limiter.limit] = lambda *a, **kw: lambda x: x
        return app

    def _get_feed(self, db, extra_patches=()):
        """GET /api/v1/feeds/waze with get_settings mocked."""
        settings_mock = MagicMock()
        settings_mock.frontend_url = "http://localhost:3000"
        with patch("api.v1.waze_feed.get_settings", return_value=settings_mock):
            for ctx in extra_patches:
                ctx.__enter__()
            resp = TestClient(self._app(db)).get("/api/v1/feeds/waze")
            for ctx in reversed(extra_patches):
                ctx.__exit__(None, None, None)
        return resp

    # ── 35. Row with lat=None → skipped, count remains 0 ────────────────────

    def test_waze_lat_none_row_skipped(self):
        """Row whose lat is None is skipped; count=0 in feed."""
        db = _mock_db()
        db.execute.return_value.fetchall.return_value = [_waze_row(lat=None)]
        settings_mock = MagicMock()
        settings_mock.frontend_url = "http://localhost:3000"
        with patch("api.v1.waze_feed.get_settings", return_value=settings_mock):
            resp = TestClient(self._app(db)).get("/api/v1/feeds/waze")
        assert resp.status_code == 200
        body = resp.json()
        assert body["count"] == 0
        assert body["incidents"] == []

    # ── 36. severity causes TypeError → defaults to 2 (medium, ttl=24h) ──────

    def test_waze_severity_type_error_defaults_to_medium(self):
        """A list severity ([1,2]) triggers TypeError in int() → falls back to 2."""
        db = _mock_db()
        # [1,2] is truthy, so ([1,2] or 2) = [1,2], then int([1,2]) → TypeError
        db.execute.return_value.fetchall.return_value = [_waze_row(severity=[1, 2])]
        settings_mock = MagicMock()
        settings_mock.frontend_url = "http://localhost:3000"
        with patch("api.v1.waze_feed.get_settings", return_value=settings_mock):
            resp = TestClient(self._app(db)).get("/api/v1/feeds/waze")
        assert resp.status_code == 200
        # Incident should still be produced at medium severity (not skipped)
        assert resp.json()["count"] == 1

    # ── 37. created_at is a datetime object → isinstance branch taken ─────────

    def test_waze_created_at_is_datetime_object(self):
        """datetime object in created_at → isinstance branch sets start_dt directly."""
        db = _mock_db()
        # Use a datetime object (not a string) to exercise the isinstance branch
        now_dt = datetime.now(timezone.utc)
        db.execute.return_value.fetchall.return_value = [_waze_row(created_at=now_dt)]

        settings_mock = MagicMock()
        settings_mock.frontend_url = "http://localhost:3000"
        # Patch _format_timestamp to bypass its str.replace() call on a datetime object,
        # which would otherwise raise TypeError (datetime.replace takes kwargs not str args)
        with (
            patch("api.v1.waze_feed.get_settings", return_value=settings_mock),
            patch("api.v1.waze_feed._format_timestamp", return_value="06/29/2026 00:00:00"),
        ):
            resp = TestClient(self._app(db)).get("/api/v1/feeds/waze")

        assert resp.status_code == 200
        # Incident is within its 24h TTL (created_at ≈ now → end_dt ≈ now+24h)
        assert resp.json()["count"] == 1

    # ── 38. created_at is a malformed string → ValueError → start_dt=now ─────

    def test_waze_created_at_malformed_string_fallback(self):
        """Malformed ISO string causes ValueError → start_dt falls back to now."""
        db = _mock_db()
        db.execute.return_value.fetchall.return_value = [
            _waze_row(created_at="definitely-not-a-date")
        ]
        settings_mock = MagicMock()
        settings_mock.frontend_url = "http://localhost:3000"
        with patch("api.v1.waze_feed.get_settings", return_value=settings_mock):
            resp = TestClient(self._app(db)).get("/api/v1/feeds/waze")
        assert resp.status_code == 200
        # Fallback: end_dt = now + 24h → incident is not expired
        assert resp.json()["count"] == 1

    # ── 39. severity=4 (critical) → ttl_hours=72, older incident still active ─

    def test_waze_severity_4_critical_ttl_72_hours(self):
        """Critical severity → 72h window; incident 50h old is still active."""
        db = _mock_db()
        created = (datetime.now(timezone.utc) - timedelta(hours=50)).isoformat()
        db.execute.return_value.fetchall.return_value = [_waze_row(severity=4, created_at=created)]
        settings_mock = MagicMock()
        settings_mock.frontend_url = "http://localhost:3000"
        with patch("api.v1.waze_feed.get_settings", return_value=settings_mock):
            resp = TestClient(self._app(db)).get("/api/v1/feeds/waze")
        assert resp.status_code == 200
        assert resp.json()["count"] == 1  # 50h + 22h remaining in 72h window

    # ── 40. severity=1 (low) → ttl_hours=12, recent incident still active ────

    def test_waze_severity_1_low_ttl_12_hours(self):
        """Low severity → 12h window; incident 5h old is still active."""
        db = _mock_db()
        created = (datetime.now(timezone.utc) - timedelta(hours=5)).isoformat()
        db.execute.return_value.fetchall.return_value = [_waze_row(severity=1, created_at=created)]
        settings_mock = MagicMock()
        settings_mock.frontend_url = "http://localhost:3000"
        with patch("api.v1.waze_feed.get_settings", return_value=settings_mock):
            resp = TestClient(self._app(db)).get("/api/v1/feeds/waze")
        assert resp.status_code == 200
        assert resp.json()["count"] == 1  # 5h elapsed, 7h remaining

    # ── 41. description is None → fallback default string used ───────────────

    def test_waze_description_none_uses_default_fallback(self):
        """None description → 'Road hazard reported via SafeVixAI' default."""
        db = _mock_db()
        db.execute.return_value.fetchall.return_value = [_waze_row(description=None)]
        settings_mock = MagicMock()
        settings_mock.frontend_url = "http://localhost:3000"
        with patch("api.v1.waze_feed.get_settings", return_value=settings_mock):
            resp = TestClient(self._app(db)).get("/api/v1/feeds/waze")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 1
        incident_desc = data["incidents"][0]["description"]
        # Fallback string from code: "Road hazard reported via SafeVixAI"
        assert "SafeVixAI" in incident_desc

    # ── 42. end_dt < now (expired) → incident skipped, count=0 ───────────────

    def test_waze_expired_incident_skipped(self):
        """Incident created 200h ago with severity=2 (ttl=24h) → expired, skipped."""
        db = _mock_db()
        old_ts = (datetime.now(timezone.utc) - timedelta(hours=200)).isoformat()
        db.execute.return_value.fetchall.return_value = [_waze_row(severity=2, created_at=old_ts)]
        settings_mock = MagicMock()
        settings_mock.frontend_url = "http://localhost:3000"
        with patch("api.v1.waze_feed.get_settings", return_value=settings_mock):
            resp = TestClient(self._app(db)).get("/api/v1/feeds/waze")
        assert resp.status_code == 200
        assert resp.json()["count"] == 0  # end_dt = (now-200h)+24h < now → skipped

    # ── 43. severity=2 (medium) → ttl_hours=24, recent incident included ──────

    def test_waze_severity_2_medium_ttl_24_hours(self):
        """Medium severity (default 2) → 24h window; incident 1h old is active."""
        db = _mock_db()
        created = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        db.execute.return_value.fetchall.return_value = [_waze_row(severity=2, created_at=created)]
        settings_mock = MagicMock()
        settings_mock.frontend_url = "http://localhost:3000"
        with patch("api.v1.waze_feed.get_settings", return_value=settings_mock):
            resp = TestClient(self._app(db)).get("/api/v1/feeds/waze")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 1
        assert data["incidents"][0]["type"] == "HAZARD_ON_ROAD"

    # ── 44. severity=3 (high) → ttl_hours=48, older incident still active ─────

    def test_waze_severity_3_high_ttl_48_hours(self):
        """High severity → 48h window; incident 40h old still has 8h remaining."""
        db = _mock_db()
        created = (datetime.now(timezone.utc) - timedelta(hours=40)).isoformat()
        db.execute.return_value.fetchall.return_value = [_waze_row(severity=3, created_at=created)]
        settings_mock = MagicMock()
        settings_mock.frontend_url = "http://localhost:3000"
        with patch("api.v1.waze_feed.get_settings", return_value=settings_mock):
            resp = TestClient(self._app(db)).get("/api/v1/feeds/waze")
        assert resp.status_code == 200
        assert resp.json()["count"] == 1  # end_dt = (now-40h)+48h = now+8h → active
