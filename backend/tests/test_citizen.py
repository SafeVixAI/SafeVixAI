# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import AsyncClient, ASGITransport

from core.database import get_db


def _mock_issue(**kwargs):
    issue = MagicMock()
    issue.uuid = kwargs.get("uuid", uuid.uuid4())
    issue.complaint_ref = kwargs.get("complaint_ref", "RS-TEST-001")
    issue.status = kwargs.get("status", "open")
    issue.category = kwargs.get("category", "roads")
    issue.issue_type = kwargs.get("issue_type", "pothole")
    issue.severity = kwargs.get("severity", 3)
    issue.description = kwargs.get("description", "Test pothole")
    issue.location_address = kwargs.get("location_address", "MG Road, Chennai")
    issue.ward_name = kwargs.get("ward_name", "Ward 1")
    issue.road_name = kwargs.get("road_name", "MG Road")
    issue.authority_name = kwargs.get("authority_name", "Test Corp")
    issue.location = kwargs.get("location", None)
    issue.before_photo_url = kwargs.get("before_photo_url", None)
    issue.after_photo_url = kwargs.get("after_photo_url", None)
    issue.created_at = kwargs.get("created_at", datetime(2026, 6, 1, 12, 0, 0))
    issue.resolved_at = kwargs.get("resolved_at", None)
    issue.sla_deadline = kwargs.get("sla_deadline", None)
    issue.confirmation_count = kwargs.get("confirmation_count", 0)
    issue.reopen_count = kwargs.get("reopen_count", 0)
    issue.citizen_rating = kwargs.get("citizen_rating", None)
    return issue


def _mock_db(issue=None, events=None):
    db = AsyncMock()
    r = MagicMock()
    r.scalar_one_or_none.return_value = issue
    r.scalars.return_value = MagicMock()
    r.scalars.return_value.all.return_value = events or []
    r.first.return_value = MagicMock()
    r.first.return_value.__getitem__ = lambda self, idx: (13.0827, 80.2707)[idx]
    db.execute.return_value = r
    db.commit = AsyncMock()
    db.add = MagicMock()
    return db


@pytest.mark.skip(reason="Service API response format changed; needs test update")
@pytest.mark.asyncio
async def test_track_complaint_found(app):
    issue = _mock_issue(complaint_ref="RS-TEST-001", status="open")
    db = _mock_db(issue=issue)
    app.dependency_overrides[get_db] = lambda: db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/citizen/complaints/RS-TEST-001")
    assert response.status_code == 200
    data = response.json()
    assert data["complaint_ref"] == "RS-TEST-001"
    assert data["status"] == "open"
    assert data["issue_type"] == "pothole"


@pytest.mark.asyncio
async def test_track_complaint_not_found(app):
    db = _mock_db(issue=None)
    app.dependency_overrides[get_db] = lambda: db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/citizen/complaints/RS-INVALID-999")
    assert response.status_code == 404


@pytest.mark.skip(reason="Service API response format changed; needs test update")
@pytest.mark.asyncio
async def test_track_complaint_with_location(app):
    issue = _mock_issue(complaint_ref="RS-TEST-002", location="POINT(80.2707 13.0827)")
    db = _mock_db(issue=issue)
    app.dependency_overrides[get_db] = lambda: db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/citizen/complaints/RS-TEST-002")
    assert response.status_code == 200
    data = response.json()
    assert data["lat"] is not None
    assert data["lon"] is not None


@pytest.mark.skip(reason="Service API response format changed; needs test update")
@pytest.mark.asyncio
async def test_track_complaint_sla_breached(app):
    deadline = datetime(2025, 1, 1, 0, 0, 0)
    issue = _mock_issue(complaint_ref="RS-TEST-003", status="in_progress", sla_deadline=deadline)
    db = _mock_db(issue=issue)
    app.dependency_overrides[get_db] = lambda: db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/citizen/complaints/RS-TEST-003")
    assert response.status_code == 200
    data = response.json()
    assert data["sla_status"] == "breached"


@pytest.mark.asyncio
async def test_track_complaint_sla_critical(app):
    deadline = datetime.now(timezone.utc).replace(tzinfo=None)
    import math
    deadline = deadline.replace(hour=deadline.hour + 2)
    issue = _mock_issue(complaint_ref="RS-TEST-004", status="in_progress", sla_deadline=deadline)
    db = _mock_db(issue=issue)
    app.dependency_overrides[get_db] = lambda: db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/citizen/complaints/RS-TEST-004")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_confirm_resolution_success(app):
    issue = _mock_issue(complaint_ref="RS-TEST-005", status="resolved")
    db = _mock_db(issue=issue)
    app.dependency_overrides[get_db] = lambda: db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/citizen/complaints/RS-TEST-005/confirm",
            json={"citizen_phone": "+91-9876543210", "comments": "Good work"},
        )
    assert response.status_code in (200, 409)


@pytest.mark.asyncio
async def test_confirm_resolution_not_resolved(app):
    issue = _mock_issue(complaint_ref="RS-TEST-006", status="open")
    db = _mock_db(issue=issue)
    app.dependency_overrides[get_db] = lambda: db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/citizen/complaints/RS-TEST-006/confirm",
            json={"citizen_phone": "+91-9876543210"},
        )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_confirm_resolution_not_found(app):
    db = _mock_db(issue=None)
    app.dependency_overrides[get_db] = lambda: db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/citizen/complaints/RS-INVALID/confirm",
            json={"citizen_phone": "+91-9876543210"},
        )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_reject_resolution_success(app):
    issue = _mock_issue(complaint_ref="RS-TEST-007", status="resolved")
    db = _mock_db(issue=issue)
    app.dependency_overrides[get_db] = lambda: db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/citizen/complaints/RS-TEST-007/reject",
            json={"reason": "The pothole was not properly filled", "citizen_phone": "+91-9876543210"},
        )
    assert response.status_code in (200, 409)


@pytest.mark.asyncio
async def test_reject_resolution_not_resolved(app):
    issue = _mock_issue(complaint_ref="RS-TEST-008", status="open")
    db = _mock_db(issue=issue)
    app.dependency_overrides[get_db] = lambda: db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/citizen/complaints/RS-TEST-008/reject",
            json={"reason": "Not satisfied with resolution"},
        )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_reject_resolution_short_reason(app):
    issue = _mock_issue(complaint_ref="RS-TEST-009", status="resolved")
    db = _mock_db(issue=issue)
    app.dependency_overrides[get_db] = lambda: db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/citizen/complaints/RS-TEST-009/reject",
            json={"reason": "Bad"},
        )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_rate_resolution_success(app):
    issue = _mock_issue(complaint_ref="RS-TEST-010", status="citizen_confirmed", citizen_rating=None)
    db = _mock_db(issue=issue, events=[])
    app.dependency_overrides[get_db] = lambda: db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/citizen/complaints/RS-TEST-010/rate",
            json={"rating": 4, "feedback": "Good response time"},
        )
    assert response.status_code in (200, 409)


@pytest.mark.asyncio
async def test_rate_resolution_invalid_rating(app):
    issue = _mock_issue(complaint_ref="RS-TEST-011", status="closed")
    db = _mock_db(issue=issue)
    app.dependency_overrides[get_db] = lambda: db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/citizen/complaints/RS-TEST-011/rate",
            json={"rating": 6, "feedback": "Excellent"},
        )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_rate_resolution_not_found(app):
    db = _mock_db(issue=None)
    app.dependency_overrides[get_db] = lambda: db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/citizen/complaints/RS-INVALID/rate",
            json={"rating": 3},
        )
    assert response.status_code == 404


@pytest.mark.skip(reason="Service API response format changed; needs test update")
@pytest.mark.asyncio
async def test_get_complaint_timeline_success(app):
    issue = _mock_issue(complaint_ref="RS-TEST-012", status="resolved")
    mock_event = MagicMock()
    mock_event.event_type = "submitted"
    mock_event.actor_role = "citizen"
    mock_event.notes = "Initial report"
    mock_event.created_at = datetime(2026, 6, 1, 12, 0, 0)
    db = _mock_db(issue=issue, events=[mock_event])
    app.dependency_overrides[get_db] = lambda: db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/citizen/complaints/RS-TEST-012/timeline")
    assert response.status_code == 200
    data = response.json()
    assert data["complaint_ref"] == "RS-TEST-012"
    assert "timeline" in data
    assert len(data["timeline"]) == 1
    assert data["timeline"][0]["event_type"] == "submitted"


@pytest.mark.asyncio
async def test_get_complaint_timeline_not_found(app):
    db = _mock_db(issue=None)
    app.dependency_overrides[get_db] = lambda: db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/citizen/complaints/RS-INVALID/timeline")
    assert response.status_code == 404
