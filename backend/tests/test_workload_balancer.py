# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

import math
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from models.officer import Officer
from services.workload_balancer import (
    OfficerScore,
    WorkloadBalancer,
    _haversine_km,
)


class TestHaversineKm:
    def test_same_point_zero(self):
        assert _haversine_km(13.0827, 80.2707, 13.0827, 80.2707) == 0.0

    def test_one_degree_lat_approx_111km(self):
        dist = _haversine_km(13.0, 80.0, 14.0, 80.0)
        assert 110.0 < dist < 112.0

    def test_symmetric(self):
        d1 = _haversine_km(13.0, 80.0, 14.0, 81.0)
        d2 = _haversine_km(14.0, 81.0, 13.0, 80.0)
        assert math.isclose(d1, d2, rel_tol=1e-9)

    def test_chennai_to_delhi(self):
        dist = _haversine_km(13.0827, 80.2707, 28.6139, 77.2090)
        assert 1700 < dist < 1900

    def test_small_distance(self):
        dist = _haversine_km(13.0, 80.0, 13.001, 80.0)
        assert 0.05 < dist < 0.2

    def test_antipodal(self):
        dist = _haversine_km(0, 0, 0, 180)
        assert 19900 < dist < 20100


class TestOfficerScore:
    def test_dataclass_all_fields(self):
        s = OfficerScore(
            officer_id="off-001",
            officer_name="Ravi Kumar",
            department="Traffic",
            ward_id="ward_050",
            current_workload=3,
            is_on_shift=True,
            distance_km=1.5,
            composite_score=95.0,
            reasons=["Ward match", "Low workload"],
        )
        assert s.officer_id == "off-001"
        assert s.officer_name == "Ravi Kumar"
        assert s.department == "Traffic"
        assert s.ward_id == "ward_050"
        assert s.current_workload == 3
        assert s.is_on_shift is True
        assert s.distance_km == 1.5
        assert s.composite_score == 95.0
        assert s.reasons == ["Ward match", "Low workload"]

    def test_dataclass_none_ward_and_distance(self):
        s = OfficerScore(
            officer_id="off-002",
            officer_name="Priya",
            department="Police",
            ward_id=None,
            current_workload=0,
            is_on_shift=False,
            distance_km=None,
            composite_score=50.0,
            reasons=["General"],
        )
        assert s.ward_id is None
        assert s.distance_km is None


class TestWorkloadBalancer:
    @pytest.mark.asyncio
    async def test_find_best_officer_no_officers(self):
        db = MagicMock()
        mock_officer_result = MagicMock()
        mock_officer_result.scalars.return_value.all.return_value = []
        db.execute = AsyncMock(return_value=mock_officer_result)

        result = await WorkloadBalancer.find_best_officer(
            db, complaint_lat=13.0, complaint_lon=80.0
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_find_best_officer_returns_highest_scored(self):
        db = MagicMock()

        officer1 = MagicMock(spec=Officer)
        officer1.id = "off-1"
        officer1.name = "A"
        officer1.department = "Traffic"
        officer1.ward_id = "WARD-1"
        officer1.is_active = True
        officer1.last_checkin = None
        officer1.last_location = None

        officer2 = MagicMock(spec=Officer)
        officer2.id = "off-2"
        officer2.name = "B"
        officer2.department = "Traffic"
        officer2.ward_id = None
        officer2.is_active = True
        officer2.last_checkin = None
        officer2.last_location = None

        mock_officer_result = MagicMock()
        mock_officer_result.scalars.return_value.all.return_value = [officer1, officer2]
        mock_workload_result = MagicMock()
        mock_workload_result.all.return_value = [("off-1", 2), ("off-2", 5)]

        db.execute = AsyncMock(side_effect=[mock_officer_result, mock_workload_result])

        result = await WorkloadBalancer.find_best_officer(
            db,
            complaint_lat=13.0,
            complaint_lon=80.0,
            ward_id="WARD-1",
            department="Traffic",
        )
        assert result is not None
        assert result.officer_id == "off-1"
        assert result.composite_score >= 100.0

    @pytest.mark.asyncio
    async def test_workload_skip_overloaded_officers(self):
        db = MagicMock()

        officer = MagicMock(spec=Officer)
        officer.id = "off-overloaded"
        officer.name = "Overloaded"
        officer.department = "Traffic"
        officer.ward_id = None
        officer.is_active = True
        officer.last_checkin = None
        officer.last_location = None

        mock_officer_result = MagicMock()
        mock_officer_result.scalars.return_value.all.return_value = [officer]
        mock_workload_result = MagicMock()
        mock_workload_result.all.return_value = [("off-overloaded", 15)]

        db.execute = AsyncMock(side_effect=[mock_officer_result, mock_workload_result])

        result = await WorkloadBalancer.find_best_officer(
            db, complaint_lat=13.0, complaint_lon=80.0
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_department_filter_passed_to_officers(self):
        db = MagicMock()

        officer = MagicMock(spec=Officer)
        officer.id = "off-traffic"
        officer.name = "Traffic-Officer"
        officer.department = "Traffic"
        officer.ward_id = None
        officer.is_active = True
        officer.last_checkin = None
        officer.last_location = None

        mock_officer_result = MagicMock()
        mock_officer_result.scalars.return_value.all.return_value = [officer]
        mock_workload_result = MagicMock()
        mock_workload_result.all.return_value = []

        db.execute = AsyncMock(side_effect=[mock_officer_result, mock_workload_result])

        result = await WorkloadBalancer.find_best_officer(
            db, complaint_lat=13.0, complaint_lon=80.0, department="Traffic"
        )
        assert result is not None
        assert result.department == "Traffic"

    @pytest.mark.asyncio
    async def test_ward_match_adds_25_points(self):
        db = MagicMock()

        officer = MagicMock(spec=Officer)
        officer.id = "off-ward"
        officer.name = "Ward-Officer"
        officer.department = "Traffic"
        officer.ward_id = "WARD-01"
        officer.is_active = True
        officer.last_checkin = None
        officer.last_location = None

        mock_officer_result = MagicMock()
        mock_officer_result.scalars.return_value.all.return_value = [officer]
        mock_workload_result = MagicMock()
        mock_workload_result.all.return_value = [("off-ward", 0)]

        db.execute = AsyncMock(side_effect=[mock_officer_result, mock_workload_result])

        result = await WorkloadBalancer.find_best_officer(
            db,
            complaint_lat=13.0,
            complaint_lon=80.0,
            ward_id="WARD-01",
        )
        assert result is not None
        assert "Ward officer match" in result.reasons

    @pytest.mark.asyncio
    async def test_recent_checkin_gives_shift_bonus(self):
        db = MagicMock()

        officer = MagicMock(spec=Officer)
        officer.id = "off-checkin"
        officer.name = "Checked-In"
        officer.department = "Traffic"
        officer.ward_id = None
        officer.is_active = True
        officer.last_checkin = datetime.now(UTC) - timedelta(minutes=30)
        officer.last_location = None

        mock_officer_result = MagicMock()
        mock_officer_result.scalars.return_value.all.return_value = [officer]
        mock_workload_result = MagicMock()
        mock_workload_result.all.return_value = [("off-checkin", 1)]

        db.execute = AsyncMock(side_effect=[mock_officer_result, mock_workload_result])

        result = await WorkloadBalancer.find_best_officer(
            db, complaint_lat=13.0, complaint_lon=80.0
        )
        assert result is not None
        assert "Recently checked in" in result.reasons

    @pytest.mark.asyncio
    async def test_severity_urgency_bonus(self):
        db = MagicMock()

        officer = MagicMock(spec=Officer)
        officer.id = "off-urgent"
        officer.name = "Available"
        officer.department = "Traffic"
        officer.ward_id = None
        officer.is_active = True
        officer.last_checkin = None
        officer.last_location = None

        mock_officer_result = MagicMock()
        mock_officer_result.scalars.return_value.all.return_value = [officer]
        mock_workload_result = MagicMock()
        mock_workload_result.all.return_value = [("off-urgent", 0)]

        db.execute = AsyncMock(side_effect=[mock_officer_result, mock_workload_result])

        result = await WorkloadBalancer.find_best_officer(
            db, complaint_lat=13.0, complaint_lon=80.0, severity=5
        )
        assert result is not None
        assert "Available for urgent assignment" in result.reasons

    @pytest.mark.asyncio
    async def test_general_availability_fallback(self):
        db = MagicMock()

        officer = MagicMock(spec=Officer)
        officer.id = "off-gen"
        officer.name = "General"
        officer.department = "Traffic"
        officer.ward_id = None
        officer.is_active = True
        officer.last_checkin = datetime.now(UTC) - timedelta(hours=10)
        officer.last_location = None

        mock_officer_result = MagicMock()
        mock_officer_result.scalars.return_value.all.return_value = [officer]
        mock_workload_result = MagicMock()
        mock_workload_result.all.return_value = [("off-gen", 7)]

        db.execute = AsyncMock(side_effect=[mock_officer_result, mock_workload_result])

        result = await WorkloadBalancer.find_best_officer(
            db, complaint_lat=13.0, complaint_lon=80.0
        )
        assert result is not None
        assert result.reasons == ["General availability"]

    @pytest.mark.asyncio
    async def test_light_workload_reason(self):
        db = MagicMock()

        officer = MagicMock(spec=Officer)
        officer.id = "off-light"
        officer.name = "Light"
        officer.department = "Traffic"
        officer.ward_id = None
        officer.is_active = True
        officer.last_checkin = None
        officer.last_location = None

        mock_officer_result = MagicMock()
        mock_officer_result.scalars.return_value.all.return_value = [officer]
        mock_workload_result = MagicMock()
        mock_workload_result.all.return_value = [("off-light", 3)]

        db.execute = AsyncMock(side_effect=[mock_officer_result, mock_workload_result])

        result = await WorkloadBalancer.find_best_officer(
            db, complaint_lat=13.0, complaint_lon=80.0
        )
        assert result is not None
        assert "Light workload" in " ".join(result.reasons)

    @pytest.mark.asyncio
    async def test_no_current_workload_reason(self):
        db = MagicMock()

        officer = MagicMock(spec=Officer)
        officer.id = "off-zero"
        officer.name = "Zero"
        officer.department = "Traffic"
        officer.ward_id = None
        officer.is_active = True
        officer.last_checkin = None
        officer.last_location = None

        mock_officer_result = MagicMock()
        mock_officer_result.scalars.return_value.all.return_value = [officer]
        mock_workload_result = MagicMock()
        mock_workload_result.all.return_value = [("off-zero", 0)]

        db.execute = AsyncMock(side_effect=[mock_officer_result, mock_workload_result])

        result = await WorkloadBalancer.find_best_officer(
            db, complaint_lat=13.0, complaint_lon=80.0
        )
        assert result is not None
        assert "No current workload" in result.reasons
